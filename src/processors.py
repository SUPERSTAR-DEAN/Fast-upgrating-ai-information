from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from src.models import NewsItem
from src.utils import normalize_url


def weekly_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=6)
    start = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    end = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
    return start, end


def deduplicate_items(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    deduped: list[NewsItem] = []

    for item in sorted(items, key=lambda x: x.published_at or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True):
        normalized = normalize_url(item.url)
        title_key = " ".join(item.title.lower().split())
        signature = hashlib.sha1(f"{item.category}|{normalized}|{title_key}".encode("utf-8")).hexdigest()
        if signature in seen:
            continue
        seen.add(signature)
        item.url = normalized
        deduped.append(item)
    return deduped


def filter_items_by_date(items: list[NewsItem], start: datetime, end: datetime) -> list[NewsItem]:
    result: list[NewsItem] = []
    for item in items:
        if item.published_at is None:
            result.append(item)
            continue
        if start <= item.published_at <= end:
            result.append(item)
    return result
