from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    email_to: str
    email_from: str


@dataclass
class AppConfig:
    repo_root: Path
    data_dir: Path
    template_dir: Path
    sources_file: Path
    use_llm_summary: bool
    llm_api_url: str | None
    llm_api_key: str | None


def load_sources(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("sources", [])


def load_app_config(repo_root: Path) -> AppConfig:
    return AppConfig(
        repo_root=repo_root,
        data_dir=repo_root / "data",
        template_dir=repo_root / "templates",
        sources_file=repo_root / "config" / "sources.yaml",
        use_llm_summary=os.getenv("USE_LLM_SUMMARY", "false").lower() == "true",
        llm_api_url=os.getenv("LLM_API_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
    )


def load_smtp_config() -> SMTPConfig:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    email_to = os.getenv("EMAIL_TO") or "ycydean@gmail.com"
    email_from = os.getenv("EMAIL_FROM") or username

    missing = [
        name
        for name, value in {
            "SMTP_HOST": host,
            "SMTP_USERNAME": username,
            "SMTP_PASSWORD": password,
            "EMAIL_TO": email_to,
            "EMAIL_FROM": email_from,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required SMTP configuration: {', '.join(missing)}")

    return SMTPConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        email_to=email_to,
        email_from=email_from,
    )
