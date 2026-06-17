import requests

from models import Match
from sqlalchemy import select
from sqlalchemy.orm import Session

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
        with Session(self.engine) as session:
            matches = []

            for i in data:
                one_match = session.get(Match, i["match_id"])
                if one_match:
                    one_match = self.update_matches(one_match, i)
                else:
                    one_match = Match(**i)

                matches.append(one_match)

            session.add_all(matches)
            session.commit()

    def collect_matches(self):
        response = self.get_matches()

        if response.status_code == 200:
            self.save_matches(response.json())

            return True
        
        return False