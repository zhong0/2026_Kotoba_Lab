"""worker 的 Docker healthcheck：heartbeat 檔在時限內更新過 → exit 0（健康），否則 exit 1。

run_local 每次成功向 SQS 拉訊息（含沒拉到）就更新 heartbeat；
long polling 最多 20 秒一輪，所以正常運作時一定在時限內更新。
SQS 連不上或迴圈卡死時 heartbeat 停止更新 → unhealthy。

刻意不 import app 其他模組，讓每次檢查都很輕量。
"""
import sys
import time
from pathlib import Path

HEARTBEAT_FILE = Path("/tmp/worker-heartbeat")
HEARTBEAT_MAX_AGE_SECONDS = 60


def is_healthy() -> bool:
    try:
        age = time.time() - HEARTBEAT_FILE.stat().st_mtime
    except FileNotFoundError:
        return False
    return age <= HEARTBEAT_MAX_AGE_SECONDS


if __name__ == "__main__":
    sys.exit(0 if is_healthy() else 1)
