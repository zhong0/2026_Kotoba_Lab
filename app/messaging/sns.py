import json

from app.messaging.aws import client, topic_arn


def publish(topic_name: str, body: dict) -> str:
    """發布一則訊息到 topic（所有訂閱的 queue 都會收到一份），回傳 MessageId。"""
    response = client("sns").publish(
        TopicArn=topic_arn(topic_name),
        Message=json.dumps(body, ensure_ascii=False),
    )
    return response["MessageId"]
