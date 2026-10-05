from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import app_config as config

APP_TZ = ZoneInfo(config.APP_TIMEZONE)


def now() -> datetime:
    """APP_TIMEZONE 的現在時間（timezone-aware）。"""
    return datetime.now(APP_TZ)


def today() -> date:
    """APP_TIMEZONE 的今天日期。每日 queue 名稱、comments.day 都以此為準。"""
    return now().date()
