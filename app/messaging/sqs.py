import json

from app.messaging.aws import client, queue_url


def send_message(queue_name: str, body: dict) -> str:
    """送出一則訊息，回傳 MessageId。"""
    response = client("sqs").send_message(
        QueueUrl=queue_url(queue_name),
        MessageBody=json.dumps(body, ensure_ascii=False),
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
