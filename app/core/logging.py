import json
import logging
import sys
import time

from app.core.config import app_config as config

_configured = False


class JsonFormatter(logging.Formatter):
    converter = time.gmtime  # UTC

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "logger": record.name,
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "file": record.filename,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """設定 root logger：JSON 一律輸出到 stdout（地端由 docker 收集，雲端由 CloudWatch 收集）。只會執行一次。"""
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL.upper())
    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    if name == "__main__":
        # 以 python -m 執行時 __name__ 會變成 "__main__"，改用原本的模組名稱
        spec = getattr(sys.modules["__main__"], "__spec__", None)
        if spec is not None:
            name = spec.name  # 例如 "app.workers.analyzer"
    return logging.getLogger(name)
