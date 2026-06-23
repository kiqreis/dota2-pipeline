class MatchDetailsProcessor:
    def __init__(self, collection):
        self.collection = collection

    def get_match_details(self, match_id):
        match_details = self.collection.find_one({"match_id": match_id})

        return match_details
