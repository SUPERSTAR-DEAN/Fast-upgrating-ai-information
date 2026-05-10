from __future__ import annotations

from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models import LearningDirection, NewsItem


def _build_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build_subject(start: datetime, end: datetime) -> str:
    return f"AI Weekly Digest ({start:%Y-%m-%d} ~ {end:%Y-%m-%d})"


def group_by_category(items: list[NewsItem]) -> dict[str, list[NewsItem]]:
    grouped: dict[str, list[NewsItem]] = {}
    for item in items:
        grouped.setdefault(item.category, []).append(item)
    return grouped


def render_email(
    template_dir: str,
    start: datetime,
    end: datetime,
    items: list[NewsItem],
    learning_directions: list[LearningDirection],
    failed_sources: list[str],
) -> tuple[str, str, str]:
    env = _build_env(template_dir)
    grouped = group_by_category(items)

    context = {
        "start": start,
        "end": end,
        "items": items,
        "grouped": grouped,
        "learning_directions": learning_directions,
        "failed_sources": failed_sources,
        "generated_at": datetime.utcnow(),
        "subject": build_subject(start, end),
    }

    html_body = env.get_template("email.html.j2").render(**context)
    text_body = env.get_template("email.txt.j2").render(**context)

    return context["subject"], html_body, text_body
