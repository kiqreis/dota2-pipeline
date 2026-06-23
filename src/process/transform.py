import pandas as pd


class MatchDetailsProcessor:
    def __init__(self, collection):
        self.collection = collection

    def get_match_details(self, match_id):
        match_details = self.collection.find_one({"match_id": match_id})

        return match_details

    def extract_match_details(self, data):
        columns = [
            "version",
            "match_id",
            "leagueid",
            "start_time",
            "duration",
            "series_id",
            "series_type",
            "cluster",
            "replay_salt",
            "radiant_win",
            "pre_game_duration",
            "match_seq_num",
            "tower_status_radiant",
            "tower_status_dire",
            "barracks_status_radiant",
            "barracks_status_dire",
            "first_blood_time",
            "lobby_type",
            "human_players",
            "game_mode",
            "flags",
            "engine",
            "radiant_score",
            "dire_score",
            "radiant_team_id",
            "radiant_name",
            "radiant_logo",
            "radiant_team_complete",
            "dire_team_id",
            "dire_name",
            "dire_logo",
            "dire_team_complete",
            "radiant_captain",
            "dire_captain",
            "replay_url",
            "patch",
            "region",
        ]

        data_process = {k: data.get(k) for k in columns}

        return pd.DataFrame([pd.Series(data_process)[columns]])
