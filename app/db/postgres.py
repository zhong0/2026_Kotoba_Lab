from contextlib import contextmanager
from typing import Iterator, Optional

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from app.core.config import app_config as config
from app.core.logging import get_logger

logger = get_logger(__name__)


class Postgres:
    """PostgreSQL 連線池的生命週期管理。pool 延遲到 connect() 才建立。"""

    def __init__(self, conninfo: str, min_size: int = 1, max_size: int = 5):
        self._conninfo = conninfo
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Optional[ConnectionPool] = None

    @property
    def pool(self) -> ConnectionPool:
        if self._pool is None:
            raise RuntimeError("Postgres is not connected; call connect() first")
        return self._pool

    def connect(self) -> None:
        if self._pool is not None:
            return
        pool = ConnectionPool(
            self._conninfo,
            min_size=self._min_size,
            max_size=self._max_size,
            kwargs={"row_factory": dict_row},  # 查詢結果以 dict 回傳
            open=False,
        )
        try:
            pool.open(wait=True, timeout=10)
        except PoolTimeout:
            pool.close()
            logger.error("Failed to connect to PostgreSQL within 10s")
            raise
        self._pool = pool
        logger.info("Connected to PostgreSQL successfully")

    def disconnect(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            logger.info("Disconnected from PostgreSQL")

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        """借出一條連線；區塊正常結束時 commit，發生例外時 rollback。

        同一個 with 區塊內的多個語句即為同一個 transaction。
        """
        with self.pool.connection() as conn:
            yield conn


postgres = Postgres(config.DATABASE_URL, config.DB_POOL_MIN_SIZE, config.DB_POOL_MAX_SIZE)
