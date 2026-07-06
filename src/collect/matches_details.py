from collections import deque
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

                stop_for = self.sliding_window - (now - self._timestamps[0]) + 0.01

            time.sleep(max(stop_for, 0.01))


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
    def __init__(self, mongo_collection):
        self.mongo_collection = mongo_collection
        self.proxies = PROXIES

    def get_matches_to_collect(self):
        with get_session() as session:
            matches_to_collect = session.scalars(
                select(Match).where(Match.flag_details_collected.is_(False))
            ).all()

            return matches_to_collect

    def get_match_details(self, match_id):
        endpoints = random.choice(self.proxies)
        response = requests.get(f"{URL}/{match_id}", timeout=30, proxies=endpoints)

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

        for match in matches:
            success = self.exec_one(match)

            if not success:
                time.sleep(60)
            else:
                time.sleep(1.1)
