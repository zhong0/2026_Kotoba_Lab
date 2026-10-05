import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.core.config import app_config as config
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.db.postgres import postgres
from app.db.redis import redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    postgres.connect()
    redis.connect()
    yield
    redis.disconnect()
    postgres.disconnect()


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION, lifespan=lifespan)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,  # 匿名 anon_id cookie 需要；origins 不可用 "*"
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    rid = uuid.uuid4().hex[:8]
    rid_path = f"rid={rid} path={request.url.path}"
    logger.info(f"{rid_path} start request")
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    logger.info(f"{rid_path} completed_in={process_time:.2f}ms status_code={response.status_code}")
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "error_message": exc.error_message},
    )


app.include_router(router)
