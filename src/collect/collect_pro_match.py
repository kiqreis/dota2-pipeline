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

    