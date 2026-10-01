"""analyzer：analyze-queue → 分析 → 發布到 SNS comment-analyzed（不直接寫 DB）。

收到的訊息：{"comment_id": "...", "content": "..."}
發布的訊息：{"comment_id": "...", <分析結果，見需求 4.7>}

地端：python -m app.workers.analyzer
雲端：Lambda handler 指向 app.workers.analyzer.handler
"""
from app.analysis import fake_llm
from app.core.config import app_config as config
from app.core.logging import get_logger
from app.messaging.sns import publish
from app.workers.runner import lambda_handler, run_local

logger = get_logger(__name__)


def process(body: dict) -> None:
    comment_id = body["comment_id"]
    if config.LLM_PROVIDER != "fake":
        raise NotImplementedError(f"LLM_PROVIDER={config.LLM_PROVIDER} is not implemented yet")
    result = fake_llm.analyze(body["content"])
    publish(config.ANALYZED_TOPIC_NAME, {"comment_id": comment_id, **result})
    logger.info(f"analyzed comment_id={comment_id} polarity={result['polarity']}")


handler = lambda_handler(process)

if __name__ == "__main__":
    run_local(config.ANALYZE_QUEUE_NAME, process)
