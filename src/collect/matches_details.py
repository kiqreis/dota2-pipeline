import requests
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
