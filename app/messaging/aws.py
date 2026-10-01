from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import app_config as config

# standard 模式：對節流、暫時性錯誤自動重試（含指數退避）
_BOTO_CONFIG = Config(retries={"mode": "standard", "max_attempts": 3})


@lru_cache
def client(service: str):
    """取得 boto3 client（每個 service 建一次後重用）。

    AWS_ENDPOINT_URL 有值 → 連 LocalStack，使用 secret 檔提供的帳密；
    留空 → 連真的 AWS，帳密交給 boto3 自行取得（Lambda 的 IAM Role 含 session token，
    若在此明確傳入 key/secret 會漏掉 token 而導致請求失敗）。
    """
    kwargs = {}
    if config.AWS_ENDPOINT_URL:
        kwargs = {
            "endpoint_url": config.AWS_ENDPOINT_URL,
            "aws_access_key_id": config.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": config.AWS_SECRET_ACCESS_KEY,
        }
    return boto3.client(service, region_name=config.AWS_DEFAULT_REGION, config=_BOTO_CONFIG, **kwargs)


@lru_cache
def queue_url(queue_name: str) -> str:
    """queue 名稱 → URL（SQS API 需要 URL）。"""
    return client("sqs").get_queue_url(QueueName=queue_name)["QueueUrl"]


@lru_cache
def topic_arn(topic_name: str) -> str:
    """topic 名稱 → ARN（SNS API 需要 ARN）。找不到時丟出 LookupError。"""
    paginator = client("sns").get_paginator("list_topics")
    for page in paginator.paginate():
        for topic in page["Topics"]:
            if topic["TopicArn"].rsplit(":", 1)[-1] == topic_name:
                return topic["TopicArn"]
    raise LookupError(f"SNS topic not found: {topic_name}")
