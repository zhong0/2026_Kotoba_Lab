"""手動丟一則測試訊息進 analyze-queue，驗證 analyzer → SNS → db-writer / stats-writer 的流程。

用法（在專案根目錄）：
  docker compose run --rm --no-deps -T --entrypoint /venv/bin/python app -m scripts.send_test_message "要測試的句子"

之後用 docker compose logs analyzer db-writer stats-writer 查看訊息有沒有流過去。
"""
import sys
import uuid

from app.core.config import app_config as config
from app.messaging.sqs import send_message

DEFAULT_CONTENT = "今天天氣很好，心情也跟著變好了！"

if __name__ == "__main__":
    content = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONTENT
    body = {"comment_id": str(uuid.uuid4()), "content": content}
    message_id = send_message(config.ANALYZE_QUEUE_NAME, body)
    print(f"sent message_id={message_id} comment_id={body['comment_id']} content={content}")
