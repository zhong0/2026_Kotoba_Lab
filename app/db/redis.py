from typing import Optional

from redis import Redis as RedisClient
from redis.exceptions import RedisError

from app.core.config import app_config as config
from app.core.logging import get_logger

logger = get_logger(__name__)


class Redis:
    """Redis 連線池的生命週期管理。client 延遲到 connect() 才建立。

    Redis 只放限流、鎖這類短期狀態，故障時呼叫端一律放行（fail open）：
    connect() 連不上只記 log、不丟例外，API 照常啟動；
    之後的指令失敗會丟 RedisError，由呼叫端捕捉後放行。
    """

    def __init__(self, host: str, port: int, password: str, ssl: bool, timeout: float):
        self._host = host
        self._port = port
        self._password = password
        self._ssl = ssl
        self._timeout = timeout
        self._client: Optional[RedisClient] = None

    @property
    def client(self) -> RedisClient:
        if self._client is None:
            raise RuntimeError("Redis is not connected; call connect() first")
        return self._client

    def connect(self) -> None:
        if self._client is not None:
            return
        self._client = RedisClient(
            host=self._host,
            port=self._port,
            password=self._password or None,
            ssl=self._ssl,
            socket_timeout=self._timeout,
            socket_connect_timeout=self._timeout,
            decode_responses=True,  # 回傳 str 而非 bytes
        )
        try:
            self._client.ping()
            logger.info("Connected to Redis successfully")
        except RedisError as e:
            # 不阻擋啟動：client 會在下次指令時自動重連
            logger.error(f"Redis is unavailable at startup; requests will fail open: {e}")

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")


redis = Redis(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.REDIS_PASSWORD,
    config.REDIS_SSL,
    config.REDIS_TIMEOUT_SECONDS,
)
