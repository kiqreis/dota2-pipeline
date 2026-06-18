import requests

from datetime import datetime, time
from db.session import get_session
from models import Match, get_oldest_match_id

URL = "https://api.opendota.com/api/proMatches"


class CollectorMatch:
    def __init__(self, engine):
        self.engine = engine
        self.url = URL

    def get_matches(self, **kwargs):
        response = requests.get(self.url, params=kwargs)

        return response

    def update_matches(self, d, i):
        d.match_id = i["match_id"]
        d.duration = i["duration"]
        d.start_time = i["start_time"]
        d.radiant_team_id = i["radiant_team_id"]
        d.radiant_name = i["radiant_name"]
        d.dire_team_id = i["dire_team_id"]
        d.dire_name = i["dire_name"]
        d.leagueid = i["leagueid"]
        d.league_name = i["league_name"]
        d.series_id = i["series_id"]
        d.series_type = i["series_type"]
        d.radiant_score = i["radiant_score"]
        d.dire_score = i["dire_score"]
        d.radiant_win = i["radiant_win"]
        d.version = i["version"]

        return d

    def save_matches(self, data):
        with get_session() as session:
            matches = []

            for i in data:
                one_match = session.get(Match, i["match_id"])
                if one_match:
                    one_match = self.update_matches(one_match, i)
                else:
                    one_match = Match(**i)

                matches.append(one_match)

            session.add_all(matches)

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
