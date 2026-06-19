from pymongo import MongoClient

from src.shared.settings import Settings

settings = Settings()

mongo_client = MongoClient(settings.MONGO_DB_URI)
mongo_db_name = mongo_client.get_database(settings.MONGO_DB_NAME)

match_details_collection = mongo_db_name.get_collection("match_details")

match_details_collection.create_index("match_id", unique=True)
