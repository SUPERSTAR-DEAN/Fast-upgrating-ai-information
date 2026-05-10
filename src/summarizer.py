from __future__ import annotations

import logging

import requests

from src.models import NewsItem
from src.utils import clean_text

logger = logging.getLogger(__name__)


def summarize_rule_based(item: NewsItem) -> str:
    base = item.description or item.title
    return clean_text(base, limit=170)


def summarize_with_optional_llm(item: NewsItem, use_llm: bool, llm_api_url: str | None, llm_api_key: str | None) -> str:
    if not use_llm or not llm_api_url or not llm_api_key:
        return summarize_rule_based(item)

    try:
        payload = {
            "text": f"Title: {item.title}\nDescription: {item.description}",
            "max_chars": 170,
            "language": "zh+en",
        }
        resp = requests.post(
            llm_api_url,
            json=payload,
            headers={"Authorization": f"Bearer {llm_api_key}"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        summary = data.get("summary") or data.get("text")
        if summary:
            return clean_text(summary, limit=170)
    except Exception as exc:
        logger.warning("LLM summary failed for %s: %s", item.title, exc)

    return summarize_rule_based(item)


def summarize_items(items: list[NewsItem], use_llm: bool, llm_api_url: str | None, llm_api_key: str | None) -> list[NewsItem]:
    for item in items:
        item.summary = summarize_with_optional_llm(item, use_llm, llm_api_url, llm_api_key)
    return items
