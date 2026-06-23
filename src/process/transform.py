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

    def save_match_details(self, df):
        match_id = df["match_id"].iloc[0]
        df.to_parquet(f"data/match_details/{match_id}.parquet", index=False)

    def extract_players_details(self, data):
        columns = [
            "player_slot",
            "obs_placed",
            "sen_placed",
            "creeps_stacked",
            "camps_stacked",
            "rune_pickups",
            "firstblood_claimed",
            "teamfight_participation",
            "towers_killed",
            "roshans_killed",
            "observers_placed",
            "stuns",
            "kill_streaks",
            "multi_kills",
            "pred_vict",
            "account_id",
            "party_id",
            "party_size",
            "team_number",
            "team_slot",
            "hero_id",
            "hero_variant",
            "item_0",
            "item_1",
            "item_2",
            "item_3",
            "item_4",
            "item_5",
            "backpack_0",
            "backpack_1",
            "backpack_2",
            "item_neutral",
            "item_neutral2",
            "kills",
            "deaths",
            "assists",
            "leaver_status",
            "last_hits",
            "denies",
            "gold_per_min",
            "xp_per_min",
            "level",
            "net_worth",
            "aghanims_scepter",
            "aghanims_shard",
            "moonshard",
            "hero_damage",
            "tower_damage",
            "hero_healing",
            "gold",
            "gold_spent",
            "personaname",
            "name",
            "last_login",
            "rank_tier",
            "computed_mmr",
            "is_subscriber",
            "radiant_win",
            "start_time",
            "duration",
            "cluster",
            "lobby_type",
            "game_mode",
            "is_contributor",
            "patch",
            "region",
            "isRadiant",
            "win",
            "lose",
            "total_gold",
            "total_xp",
            "kills_per_min",
            "kda",
            "abandons",
            "neutral_kills",
            "tower_kills",
            "courier_kills",
            "lane_kills",
            "hero_kills",
            "observer_kills",
            "sentry_kills",
            "roshan_kills",
            "necronomicon_kills",
            "ancient_kills",
            "buyback_count",
            "observer_uses",
            "sentry_uses",
            "lane_efficiency",
            "lane_efficiency_pct",
            "lane",
            "lane_role",
            "is_roaming",
            "actions_per_min",
            "life_state_dead",
        ]

        df_players = pd.DataFrame(data["players"])
        df_template = pd.DataFrame(columns=columns)

        df = pd.concat([df_players, df_template])[columns]
        df["match_id"] = data["match_id"]

        columns_order = ["match_id"] + columns

        df = df.reindex(columns=columns_order)

        return df
