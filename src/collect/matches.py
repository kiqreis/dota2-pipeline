import random

import requests

from datetime import datetime
import time

from sqlalchemy import select
from src.shared.settings import Settings
from src.db.session import get_session
from src.collect.models import Match, get_oldest_match_id

URL = "https://api.opendota.com/api/proMatches"

settings = Settings()
PROXIES = settings.PROXIES


class CollectorMatch:
    def __init__(self):
        self.url = URL
        self.proxies = PROXIES

    def get_matches(self, **kwargs):
        endopoint = random.choice(self.proxies)
        response = requests.get(self.url, params=kwargs, timeout=30, proxies=endopoint)

        return response

    def save_matches(self, data):
        with get_session() as session:
            ids = [i["match_id"] for i in data]

            stmt = select(Match.match_id).where(Match.match_id.in_(ids))
            existing_ids = set(session.scalars(stmt).all())

            new_matches = [
                Match(**i) for i in data if i["match_id"] not in existing_ids
            ]

            session.add_all(new_matches)

    def collect_matches(self):
        response = self.get_matches()

        if response.status_code == 200:
            self.save_matches(response.json())

            return True

        return False

    def collect_matches_until(self, date=None, from_history=True):
        if date is None:
            date = datetime.today().strftime("%Y-%m-%d")

        last_id = get_oldest_match_id() if from_history else None

        while True:
            response = self.get_matches(less_than_match_id=last_id)

            if response.status_code != 200:
                time.sleep(60)
                continue

            matches = response.json()
            valid_matches = []

            for match in matches:
                match_day = datetime.fromtimestamp(match["start_time"]).strftime(
                    "%Y-%m-%d"
                )

                if match_day < date:
                    break

                valid_matches.append(match)

            self.save_matches(valid_matches)

            oldest_match = matches[-1]

            oldest_day = datetime.fromtimestamp(oldest_match["start_time"]).strftime(
                "%Y-%m-%d"
            )

            if oldest_day < date:
                break

            last_id = oldest_match["match_id"]

        return True
