from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo.errors import AutoReconnect
from tenacity import retry, retry_if_exception_type, stop_after_attempt
import random

import requests
from sqlalchemy import select

from src.collect.proxy import ProxyRouter
from src.shared.settings import Settings, RateLimitException
from src.collect.models import Match
from src.db.session import get_session

URL = "https://api.opendota.com/api/matches"


settings = Settings()
PROXIES = settings.PROXIES

MAX_REQUESTS_PER_MINUTE = 60


def _wait_time(retry_state):
    exec = retry_state.outcome.exception()

    if isinstance(exec, RateLimitException):
        return exec.retry_after

    base_time = min(30, 2**retry_state.attempt_number)

    return base_time + random.uniform(0, 1)


def sanitize_for_mongo(data):
    MAX_INT = 9223372036854775807

    if isinstance(data, dict):
        sanitized = {}

        for k, v in data.items():
            sanitized_value = sanitize_for_mongo(v)

            if isinstance(sanitized_value, int) and sanitized_value > MAX_INT:
                sanitized[k] = str(sanitized_value)
            else:
                sanitized[k] = sanitized_value

        return sanitized

    elif isinstance(data, list):
        return [sanitize_for_mongo(i) for i in data]

    return data


class CollectorMatchDetails:
    def __init__(self, mongo_collection, max_workers):
        self.mongo_collection = mongo_collection
        self.proxies = ProxyRouter(PROXIES, MAX_REQUESTS_PER_MINUTE)
        self.max_workers = max_workers or max(1, len(PROXIES) * 2)

    def get_matches_to_collect(self):
        with get_session() as session:
            matches_to_collect = session.scalars(
                select(Match).where(Match.flag_details_collected.is_(False))
            ).all()

            return matches_to_collect

    @retry(
        stop=stop_after_attempt(6),
        wait=_wait_time,
        retry=retry_if_exception_type(
            (
                requests.RequestException,
                RateLimitException,
                ConnectionError,
                AutoReconnect,
            )
        ),
        reraise=True,
    )
    def get_match_details(self, match_id):
        endpoints, _ = self.proxies.acquire_proxy()
        response = requests.get(f"{URL}/{match_id}", timeout=30, proxies=endpoints)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", 5)
            raise RateLimitException(retry_after=retry_after)

        if response.status_code >= 500:
            response.raise_for_status()

        return response

    def insert_match_mongo(self, data):
        sanitized_data = sanitize_for_mongo(data)
        result = self.mongo_collection.insert_one(sanitized_data)

        return result

    def update_match_as_collected(self, match_id):
        with get_session() as session:
            match = session.get(Match, match_id)

            if match:
                match.flag_details_collected = True

    def exec_one(self, match_collected):
        match_id = match_collected.match_id
        response = self.get_match_details(match_id)

        if response.status_code != 200:
            return False

        self.insert_match_mongo(response.json())
        self.update_match_as_collected(match_id)

        return True

    def exec_all(self):
        matches = self.get_matches_to_collect()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.exec_one, m) for m in matches]

            for future in as_completed(futures):
                future.result()
