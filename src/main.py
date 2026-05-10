from __future__ import annotations

import json
import logging
from datetime import timezone
from pathlib import Path

from src.collector import collect_all_sources
from src.config import load_app_config, load_smtp_config, load_sources
from src.email_sender import send_email
from src.learning_plan import build_learning_directions
from src.processors import deduplicate_items, filter_items_by_date, weekly_window
from src.render import render_email
from src.summarizer import summarize_items

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _save_cache(data_dir: Path, payload: dict) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    weekly_file = data_dir / f"weekly_digest_{payload['end_date'].replace('-', '')}.json"
    latest_file = data_dir / "latest.json"
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    weekly_file.write_text(content, encoding="utf-8")
    latest_file.write_text(content, encoding="utf-8")


def run() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    app_cfg = load_app_config(repo_root)
    sources = load_sources(app_cfg.sources_file)

    start, end = weekly_window()
    logger.info("Weekly window: %s ~ %s", start.isoformat(), end.isoformat())

    items, failed_sources = collect_all_sources(sources)
    logger.info("Collected total items: %s; failed sources: %s", len(items), len(failed_sources))

    items = filter_items_by_date(items, start, end)
    items = deduplicate_items(items)
    items = summarize_items(items, app_cfg.use_llm_summary, app_cfg.llm_api_url, app_cfg.llm_api_key)
    learning_directions = build_learning_directions(items)

    subject, html_body, text_body = render_email(
        str(app_cfg.template_dir),
        start,
        end,
        items,
        learning_directions,
        failed_sources,
    )

    payload = {
        "start_date": f"{start:%Y-%m-%d}",
        "end_date": f"{end:%Y-%m-%d}",
        "generated_at": str(end.astimezone(timezone.utc)),
        "total_items": len(items),
        "failed_sources": failed_sources,
        "items": [item.to_dict() for item in items],
        "subject": subject,
    }
    _save_cache(app_cfg.data_dir, payload)

    smtp_cfg = load_smtp_config()
    send_email(smtp_cfg, subject, text_body, html_body)
    logger.info("Email sent to %s with %s items", smtp_cfg.email_to, len(items))


if __name__ == "__main__":
    run()
