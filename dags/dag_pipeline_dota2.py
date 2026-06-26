from datetime import datetime

import boto3

from airflow import DAG
from airflow.operators.python import PythonOperator


def run_collect_matches():
    from src.collect.matches import CollectorMatch

    collector = CollectorMatch()
    collector.collect_matches_until(date="2026-06-24", from_history=True)


def run_collect_matches_details():
    from src.collect.matches_details import CollectorMatchDetails
    from src.db.mongo import match_details_collection

    collector = CollectorMatchDetails(match_details_collection)
    collector.exec_all()


def run_processor():
    from src.process.transform import MatchDetailsProcessor
    from src.db.mongo import match_details_collection

    processor = MatchDetailsProcessor(match_details_collection)
    processor.process_all()


def run_sender():
    from src.storage.s3s import S3S
    from src.shared.settings import Settings

    settings = Settings()
    client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        region_name=settings.AWS_REGION,
    )

    sender = S3S(client)
    sender.upload_all()


with DAG(
    dag_id="pipeline_dota2",
    start_date=datetime(2025, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    tags=["dota2"],
) as dag:

    t1 = PythonOperator(task_id="collect_matches", python_callable=run_collect_matches)
    t2 = PythonOperator(
        task_id="collect_matches_details", python_callable=run_collect_matches_details
    )
    t3 = PythonOperator(task_id="process_transform", python_callable=run_processor)
    t4 = PythonOperator(task_id="send_to_s3", python_callable=run_sender)

    t1 >> t2 >> t3 >> t4
