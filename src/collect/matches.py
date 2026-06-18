import requests

from datetime import datetime, time

from sqlalchemy import select
from src.db.session import get_session
from src.collect.models import Match, get_oldest_match_id

URL = "https://api.opendota.com/api/proMatches"


class CollectorMatch:
    def __init__(self):
        self.url = URL

    def get_matches(self, **kwargs):
        response = requests.get(self.url, params=kwargs)

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
        last_id = None

        if from_history:
            last_id = get_oldest_match_id(self.engine)

        match_date = datetime.now().strftime("%Y-%m-%d")

        while date <= match_date:
            response = self.get_matches(less_than_match_id=last_id)

            if response.status_code != 200:
                time.sleep(60)
                continue

            matches = response.json()
            self.save_matches(matches)
            older_match = matches[-1]

            match_date = datetime.fromtimestamp(older_match["start_time"]).strftime(
                "%Y-%m-%d"
            )

            last_id = older_match["match_id"]

        return True
