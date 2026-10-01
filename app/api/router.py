from fastapi import APIRouter
from fastapi.responses import JSONResponse
from psycopg import Error as PsycopgError
from psycopg_pool import PoolTimeout

from app.core.config import app_config as config
from app.core.logging import get_logger
from app.db.postgres import postgres

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
def health():
    """健康檢查：實際對資料庫執行 SELECT 1，連不上時回 503（供 Docker / 負載平衡器判斷）。"""
    body = {"app": config.APP_NAME, "version": config.APP_VERSION}
    try:
        with postgres.connection() as conn:
            conn.execute("SELECT 1")
    except (PsycopgError, PoolTimeout) as e:
        logger.error(f"health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unavailable", **body})
    return {"status": "ok", **body}
