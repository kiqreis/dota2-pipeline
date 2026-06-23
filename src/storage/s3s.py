import os
import pandas as pd
import boto3

from datetime import datetime

from src.shared.settings import Settings

settings = Settings()

s3_client = boto3.client(
    "s3",
    aws_access_key=settings.AWS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION,
)


class S3S:
    def __init__(self, s3):
        self.s3 = s3
        self.data_path = "/data"

    def upload_files(self, batch_size=10_000):
        folder = os.path.join(self.data_path, "match_players_details")
        files = [i for i in os.listdir(folder) if i.endswith("parquet")]

        while len(files) > 0:
            files_process = files[:batch_size]

            dfs = [pd.read_parquet(os.path.join(folder, i)) for i in files_process]
            df = pd.concat(dfs)

            df.to_parquet("batch_match_player_details.parquet")

            now = datetime.now().strftime("%Y%m%d_%H%M%S%f")

            self.s3.upload_file(
                "batch_match_player_details.parquet",
                "datalake-raw-muci",
                f"dota2/match_player_details/{now}.parquet",
            )

            for i in files_process:
                files.remove(i)
