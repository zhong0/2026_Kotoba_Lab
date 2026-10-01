"""db-writer：db-writer-queue（訂閱 comment-analyzed）→ 把分析結果寫回 comments。

目前只記 log；第 2 階段改為以 comment_id 冪等寫入 comments（status = done）。

地端：python -m app.workers.db_writer
雲端：Lambda handler 指向 app.workers.db_writer.handler
"""
from app.core.config import app_config as config
from app.core.logging import get_logger
from app.workers.runner import lambda_handler, run_local

logger = get_logger(__name__)


def process(body: dict) -> None:
    logger.info(f"received analysis result comment_id={body['comment_id']}")


handler = lambda_handler(process)

if __name__ == "__main__":
    run_local(config.DB_WRITER_QUEUE_NAME, process)
