from __future__ import annotations

import socket
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import SMTPConfig


def _preflight_dns(host: str) -> None:
    # Fail fast with a clearer error message than smtplib/socket.gaierror
    try:
        socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValueError(
            f"SMTP_HOST DNS 解析失败: {host!r}. "
            "请检查 GitHub Actions secrets 里的 SMTP_HOST 是否为正确域名（例如 smtp.gmail.com），"
            "以及是否包含协议头（不要写成 https://...）。"
        ) from exc


def send_email(cfg: SMTPConfig, subject: str, text_body: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.email_from
    msg["To"] = cfg.email_to

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    _preflight_dns(cfg.host)

    with smtplib.SMTP(cfg.host, cfg.port, timeout=45) as server:
        server.starttls()
        server.login(cfg.username, cfg.password)
        server.sendmail(cfg.email_from, [cfg.email_to], msg.as_string())
