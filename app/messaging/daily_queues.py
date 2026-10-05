"""每日的人類留言 / AI 句子 FIFO queue：命名與建立。

每天各開一個：human-YYYY-MM-DD.fifo、ai-YYYY-MM-DD.fifo（日期為 APP_TIMEZONE）。
human queue 會在隔天作為備用再用一天，所以訊息最多保留兩天；兩天後 queue 整個刪除。
何時建立、切換、刪除由排程負責（尚未實作），這裡只提供工具函式。
"""
from datetime import date

from app.core.config import app_config as config
from app.messaging.sqs import create_fifo_queue

# 當天 + 隔天備用；AI queue 只用一天，但用同一個值即可（queue 會被整個刪除）
RETENTION_SECONDS = 2 * 24 * 60 * 60


def human_queue_name(day: date) -> str:
    return f"{config.HUMAN_QUEUE_PREFIX}-{day.isoformat()}.fifo"


def ai_queue_name(day: date) -> str:
    return f"{config.AI_QUEUE_PREFIX}-{day.isoformat()}.fifo"


def ensure_daily_queues(day: date) -> None:
    """建立指定日期的 human / ai queue（已存在則不動）。"""
    create_fifo_queue(human_queue_name(day), RETENTION_SECONDS)
    create_fifo_queue(ai_queue_name(day), RETENTION_SECONDS)
