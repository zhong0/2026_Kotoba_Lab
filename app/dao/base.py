from contextlib import contextmanager

from psycopg import Error as PsycopgError

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.db.postgres import Postgres

logger = get_logger(__name__)


class PostgresRepository:
    """各 repository 的共用基底。

    不提供通用 CRUD：每個 repository 以參數化 SQL 寫出明確的方法
    （條件 UPDATE、ON CONFLICT 等）。所有操作失敗時丟出 DatabaseError，
    由全域 exception handler 統一處理，呼叫端不需要逐一檢查 status。
    """

    table: str = ""

    def __init__(self, db: Postgres):
        self._db = db

    @contextmanager
    def _wrap_errors(self, op: str):
        try:
            yield
        except PsycopgError as e:
            msg = f"{op} failed on {self.table}: {e}"
            logger.error(msg)
            raise DatabaseError(msg) from e
