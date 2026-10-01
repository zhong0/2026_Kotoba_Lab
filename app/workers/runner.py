"""worker 的共用執行框架：業務邏輯只寫一個 process(body)，由這裡接上地端或雲端。

- 地端：run_local(queue_name, process) —— 迴圈拉訊息
- 雲端：handler = lambda_handler(process) —— 由 SQS 觸發 Lambda

process() 丟出例外 = 這則處理失敗：訊息不刪除，visibility timeout 後 SQS 重送，
超過 maxReceiveCount 次移入 DLQ。因此 process() 必須冪等（SQS 為 at-least-once）。
"""
import json
import signal
import time
from typing import Any, Callable

from botocore.exceptions import BotoCoreError, ClientError

from app.core.logging import get_logger
from app.messaging.sqs import delete_message, receive_messages
from app.workers.healthcheck import HEARTBEAT_FILE

logger = get_logger(__name__)

Process = Callable[[dict], None]

RECEIVE_ERROR_BACKOFF_SECONDS = 5


def run_local(queue_name: str, process: Process) -> None:
    """地端入口：持續從 queue 拉訊息處理，收到 SIGTERM/SIGINT 時處理完手上這批再結束。"""
    stopping = False

    def _stop(signum, _frame):
        nonlocal stopping
        stopping = True
        logger.info(f"received signal {signum}; stopping after current batch")

    signal.signal(signal.SIGTERM, _stop)  # docker stop
    signal.signal(signal.SIGINT, _stop)   # Ctrl+C

    logger.info(f"worker started: queue={queue_name}")
    while not stopping:
        try:
            messages = receive_messages(queue_name)
        except (BotoCoreError, ClientError) as e:
            # 例如 LocalStack 尚未就緒、網路中斷：稍後重試，不讓 worker 掛掉
            logger.error(f"receive failed on {queue_name}: {e}")
            time.sleep(RECEIVE_ERROR_BACKOFF_SECONDS)
            continue
        HEARTBEAT_FILE.touch()  # 能連上 SQS 才更新，供 healthcheck 判斷

        for msg in messages:
            try:
                process(json.loads(msg["Body"]))
            except Exception:
                logger.exception(f"process failed: queue={queue_name} message_id={msg['MessageId']}; will be retried")
                continue
            try:
                delete_message(queue_name, msg["ReceiptHandle"])
            except (BotoCoreError, ClientError) as e:
                # 已處理成功但刪除失敗：之後會被重送，靠 process() 冪等吸收
                logger.error(f"delete failed: queue={queue_name} message_id={msg['MessageId']}: {e}")
    logger.info(f"worker stopped: queue={queue_name}")


def lambda_handler(process: Process) -> Callable[[dict, Any], dict]:
    """雲端入口：產生 Lambda handler。

    回傳 batchItemFailures 只列出失敗的訊息，成功的由 Lambda 自動刪除
    （需在 event source mapping 開啟 ReportBatchItemFailures）。
    """

    def handler(event: dict, context: Any) -> dict:
        failures = []
        for record in event["Records"]:
            try:
                process(json.loads(record["body"]))
            except Exception:
                logger.exception(f"process failed: message_id={record['messageId']}; will be retried")
                failures.append({"itemIdentifier": record["messageId"]})
        return {"batchItemFailures": failures}

    return handler
