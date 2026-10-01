"""stats-writer：stats-queue（訂閱 comment-analyzed）→ 更新 stats_counters。

目前只記 log；第 2 階段改為與 stats_applied 同一個 transaction 冪等計數。

地端：python -m app.workers.stats_writer
雲端：Lambda handler 指向 app.workers.stats_writer.handler
"""
from app.core.config import app_config as config
from app.core.logging import get_logger
from app.workers.runner import lambda_handler, run_local

logger = get_logger(__name__)


def process(body: dict) -> None:
    logger.info(f"received analysis result comment_id={body['comment_id']}")


handler = lambda_handler(process)

if __name__ == "__main__":
    run_local(config.STATS_QUEUE_NAME, process)
