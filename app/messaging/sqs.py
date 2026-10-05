import json
from typing import Optional

from app.messaging.aws import client, queue_url


def send_message(
    queue_name: str,
    body: dict,
    group_id: Optional[str] = None,
    dedup_id: Optional[str] = None,
) -> str:
    """送出一則訊息，回傳 MessageId。

    FIFO queue 必須給 group_id 與 dedup_id（standard queue 不可給）。
    dedup_id 只在 5 分鐘內去重，真正的防重複以 DB 條件更新與唯一約束為準。
    """
    kwargs = {}
    if group_id is not None:
        kwargs["MessageGroupId"] = group_id
    if dedup_id is not None:
        kwargs["MessageDeduplicationId"] = dedup_id
    response = client("sqs").send_message(
        QueueUrl=queue_url(queue_name),
        MessageBody=json.dumps(body, ensure_ascii=False),
        **kwargs,
    )
    return response["MessageId"]


def receive_messages(queue_name: str, max_messages: int = 10, wait_seconds: int = 20) -> list[dict]:
    """收訊息（long polling：最多等 wait_seconds 秒，有訊息就立刻回傳）。

    收到的訊息在 visibility timeout 內對其他 consumer 不可見；
    處理完必須呼叫 delete_message，否則逾時後會被重送。
    """
    response = client("sqs").receive_message(
        QueueUrl=queue_url(queue_name),
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_seconds,
    )
    return response.get("Messages", [])


def delete_message(queue_name: str, receipt_handle: str) -> None:
    client("sqs").delete_message(QueueUrl=queue_url(queue_name), ReceiptHandle=receipt_handle)


def release_message(queue_name: str, receipt_handle: str) -> None:
    """不處理、立刻放回 queue（visibility timeout 設為 0），讓下一個 consumer 可以收到。"""
    client("sqs").change_message_visibility(
        QueueUrl=queue_url(queue_name),
        ReceiptHandle=receipt_handle,
        VisibilityTimeout=0,
    )


def approximate_count(queue_name: str) -> int:
    """queue 中可收取的訊息數（近似值，有幾秒延遲）。"""
    response = client("sqs").get_queue_attributes(
        QueueUrl=queue_url(queue_name),
        AttributeNames=["ApproximateNumberOfMessages"],
    )
    return int(response["Attributes"]["ApproximateNumberOfMessages"])


def create_fifo_queue(queue_name: str, retention_seconds: int) -> str:
    """建立 FIFO queue，回傳 URL。名稱必須以 .fifo 結尾；已存在且屬性相同時直接回傳 URL（冪等）。"""
    response = client("sqs").create_queue(
        QueueName=queue_name,
        Attributes={
            "FifoQueue": "true",
            "ContentBasedDeduplication": "false",  # 一律由呼叫端給 dedup_id
            "MessageRetentionPeriod": str(retention_seconds),
        },
    )
    return response["QueueUrl"]


def delete_queue(queue_name: str) -> None:
    client("sqs").delete_queue(QueueUrl=queue_url(queue_name))
    queue_url.cache_clear()  # 避免之後拿到已刪除 queue 的 URL
