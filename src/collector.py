from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dt_parser

from src.models import NewsItem
from src.utils import clean_text, normalize_url

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "weekly-ai-digest/1.0 (+https://github.com/SUPERSTAR-DEAN/Fast-upgrating-ai-information)",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = parsedate_to_datetime(str(value))
        except Exception:
            try:
                dt = dt_parser.parse(str(value))
            except Exception:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def collect_from_rss(source: dict[str, Any], timeout: int = 25) -> list[NewsItem]:
    url = source["url"]
    feed = feedparser.parse(url, request_headers=_HEADERS)
    items: list[NewsItem] = []
    for entry in feed.entries[:40]:
        link = entry.get("link")
        if not link:
            continue
        published = (
            _parse_datetime(entry.get("published"))
            or _parse_datetime(entry.get("updated"))
            or _parse_datetime(entry.get("created"))
        )
        description = entry.get("summary") or entry.get("description") or ""
        items.append(
            NewsItem(
                title=clean_text(entry.get("title", "(untitled)"), limit=180),
                url=normalize_url(link),
                source_name=source["name"],
                category=source["category"],
                published_at=published,
                description=clean_text(description, limit=500),
            )
        )
    return items


def collect_from_html_list(source: dict[str, Any], timeout: int = 25) -> list[NewsItem]:
    response = requests.get(source["url"], headers=_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    selectors = source.get("selectors", {})
    item_selector = selectors.get("item", "article a")
    anchors = soup.select(item_selector)

    items: list[NewsItem] = []
    seen: set[str] = set()
    for anchor in anchors:
        href = anchor.get("href")
        title = clean_text(anchor.get_text(" ", strip=True), limit=180)
        if not href or not title:
            continue
        link = requests.compat.urljoin(source["url"], href)
        normalized = normalize_url(link)
        if normalized in seen:
            continue
        seen.add(normalized)
        items.append(
            NewsItem(
                title=title,
                url=normalized,
                source_name=source["name"],
                category=source["category"],
                published_at=None,
                description="",
            )
        )
        if len(items) >= 25:
            break
    return items


def collect_from_github_trending(source: dict[str, Any], timeout: int = 25) -> list[NewsItem]:
    response = requests.get(source["url"], headers=_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[NewsItem] = []
    now = datetime.now(timezone.utc)

    for article in soup.select("article.Box-row")[:30]:
        repo_anchor = article.select_one("h2 a")
        if not repo_anchor:
            continue
        repo_name = clean_text(repo_anchor.get_text(" ", strip=True).replace(" ", ""), limit=120)
        href = repo_anchor.get("href")
        if not href:
            continue
        description_node = article.select_one("p")
        description = clean_text(description_node.get_text(" ", strip=True) if description_node else "", limit=400)
        language_node = article.select_one("span[itemprop='programmingLanguage']")
        language = language_node.get_text(strip=True) if language_node else "Unknown"
        stars_node = article.select_one("a.Link--muted[href$='/stargazers']")
        stars = stars_node.get_text(" ", strip=True) if stars_node else "-"
        tags = f"Language: {language}; Stars: {stars}"

        full_url = requests.compat.urljoin("https://github.com", href)
        if not any(k in (repo_name + " " + description).lower() for k in ["ai", "ml", "llm", "diffusion", "transformer", "rag", "agent", "torch"]):
            continue

        items.append(
            NewsItem(
                title=f"{repo_name} (Trending)",
                url=normalize_url(full_url),
                source_name=source["name"],
                category=source["category"],
                published_at=now,
                description=clean_text(f"{tags}. {description}", limit=500),
            )
        )
    return items


def collect_all_sources(sources: list[dict[str, Any]]) -> tuple[list[NewsItem], list[str]]:
    all_items: list[NewsItem] = []
    failed_sources: list[str] = []

    for source in sources:
        try:
            source_type = source.get("type", "rss")
            logger.info("Collecting source=%s type=%s", source.get("name"), source_type)
            if source_type == "rss":
                items = collect_from_rss(source)
            elif source_type == "github_trending":
                items = collect_from_github_trending(source)
            elif source_type == "html_list":
                items = collect_from_html_list(source)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")

            logger.info("Collected %s items from %s", len(items), source.get("name"))
            all_items.extend(items)
        except Exception as exc:
            name = source.get("name", "unknown")
            failed_sources.append(name)
            logger.warning("Failed to collect source %s: %s", name, exc)

    return all_items, failed_sources
