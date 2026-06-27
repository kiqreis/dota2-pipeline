from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="pipeline_dota2",
    start_date=datetime(2025, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    tags=["dota2"],
    params={"target_date": "2026-06-27", "from_history": True},
)
def pipeline_dota2():
    @task(task_id="collect_matches")
    def collect_matches(**ctx):
        from src.collect.matches import CollectorMatch

        collector = CollectorMatch()

        target_date = ctx["params"]["target_date"]
        from_history = ctx["params"]["from_history"]

        collector.collect_matches_until(date=target_date, from_history=from_history)

    @task(task_id="collect_matches_details")
    def collect_matches_details(**ctx):
        from src.collect.matches_details import CollectorMatchDetails
        from src.shared.settings import Settings
        from pymongo import MongoClient

        settings = Settings()
        client = MongoClient(settings.MONGO_DB_URI)
        collection = client.get_database(settings.MONGO_DB_NAME).get_collection(
            "match_details"
        )

        collector = CollectorMatchDetails(collection)

        collector.exec_all()

    @task(task_id="process_transform")
    def process_transform(**ctx):
        from src.process.transform import MatchDetailsProcessor
        from src.shared.settings import Settings
        from pymongo import MongoClient

        settings = Settings()
        client = MongoClient(settings.MONGO_DB_URI)

        collection = client.get_database(settings.MONGO_DB_NAME).get_collection(
            "match_details"
        )

        processor = MatchDetailsProcessor(collection)

        processor.process_all()

    @task(task_id="send_to_s3")
    def send_to_s3(**ctx):
        from src.storage.s3s import S3S
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook

        s3_hook = S3Hook(aws_conn_id="aws_default")
        sender = S3S(s3=s3_hook.get_conn())

        batch_size = ctx["params"].get("batch_size", 100_000)
        sender.upload_all(batch_size=batch_size)

    (
        collect_matches()
        >> collect_matches_details()
        >> process_transform()
        >> send_to_s3()
    )


dag_run = pipeline_dota2()
