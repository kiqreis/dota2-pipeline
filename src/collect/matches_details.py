import requests
import time
from sqlalchemy import select

from src.db.mongo import mongo_client
from src.collect.models import Match
from src.db.session import get_session

URL = "https://api.opendota.com/api/matches"


class CollectorMatchDetails:
    def __init__(self, sql_engine, mongo_collection):
        self.sql_engine = sql_engine
        self.mongo_collection = mongo_collection

    def get_matches_to_collect(self):
        with get_session() as session:
            matches_to_collect = session.scalars(
                select(Match).where(Match.flag_details_collected.is_(False))
            ).all()

            return matches_to_collect

    def get_match_details(self, match_id):
        response = requests.get(f"{URL}/{match_id}")

        return response

    def insert_match_mongo(self, data):
        result = self.mongo_collection.delete_one({"match_id": data["match_id"]})
        result = self.mongo_collection.insert_one(data)

        return result

    def update_match_as_collected(self, match_collected):
        with get_session() as session:
            match_collected.flag_details_collected = True

            session.add(match_collected)

    def exec_one(self, match_collected):
        response = self.get_match_details(match_collected.match_id)

        if response.status_code != 200:
            return False

        self.insert_match_mongo(response.json())
        self.update_match_as_collected(match_collected)

        return True
