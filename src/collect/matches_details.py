from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo.errors import AutoReconnect
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from collections import deque
import itertools
import random
import threading
import time

import requests
from sqlalchemy import select

from src.shared.settings import Settings
from src.collect.models import Match
from src.db.session import get_session

URL = "https://api.opendota.com/api/matches"


settings = Settings()
PROXIES = settings.PROXIES

MAX_REQUESTS_PER_MINUTE_PER_PROXY = 60
WINDOW_SECONDS = 60.0


class RateLimitException(Exception):
    def __init__(self, retry_after=5):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class ProxyRateLimiter:
    def __init__(self, max_requests, sliding_window):
        self.max_requests = max_requests
        self.sliding_window = sliding_window
        self._timestamps = deque()
        self._thread_lock = threading.Lock()

    def wait_for_slot(self):
        while True:
            with self._thread_lock:
                now = time.monotonic()

                while (
                    self._timestamps and now - self._timestamps[0] > self.sliding_window
                ):
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return

                stop_for = self.sliding_window - (now - self._timestamps[0]) + 0.01

            time.sleep(max(stop_for, 0.01))


class ProxyRouter:
    def __init__(self, proxies, max_spin: int):
        if not proxies:
            raise ValueError("PROXIES está vazio")
        self._proxies = proxies
        self._limiters = [ProxyRateLimiter(max_spin, WINDOW_SECONDS) for _ in proxies]
        self._cycle = itertools.cycle(range(len(proxies)))
        self._lock = threading.Lock()

    def acquire_proxy(self):
        with self._lock:
            i = next(self._cycle)
        proxy = self._proxies[i]
        self._limiters[i].wait_for_slot()
        return proxy, i


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
        self.proxies = ProxyRouter(PROXIES, MAX_REQUESTS_PER_MINUTE_PER_PROXY)
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
