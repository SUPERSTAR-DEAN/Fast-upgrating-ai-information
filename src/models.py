from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class NewsItem:
    title: str
    url: str
    source_name: str
    category: str
    published_at: datetime | None
    description: str
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["published_at"] = self.published_at.isoformat() if self.published_at else None
        return payload


@dataclass
class LearningDirection:
    title: str
    bullets: list[str]
