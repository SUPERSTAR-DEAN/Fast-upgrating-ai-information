from __future__ import annotations

import logging
import socket
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import SMTPConfig

logger = logging.getLogger(__name__)
SMTP_TIMEOUT_SECONDS = 30


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
    tls_context = ssl.create_default_context()
    tls_mode = "SMTP_SSL" if cfg.port == 465 else "STARTTLS"
    logger.info(
        "Preparing SMTP delivery via %s:%s using %s (from=%s, to=%s)",
        cfg.host,
        cfg.port,
        tls_mode,
        cfg.email_from,
        cfg.email_to,
    )

    try:
        if cfg.port == 465:
            with smtplib.SMTP_SSL(
                cfg.host,
                cfg.port,
                context=tls_context,
                timeout=SMTP_TIMEOUT_SECONDS,
            ) as server:
                server.login(cfg.username, cfg.password)
                server.sendmail(cfg.email_from, [cfg.email_to], msg.as_string())
        else:
            with smtplib.SMTP(cfg.host, cfg.port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.ehlo()
                server.starttls(context=tls_context)
                server.ehlo()
                server.login(cfg.username, cfg.password)
                server.sendmail(cfg.email_from, [cfg.email_to], msg.as_string())
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            f"SMTP authentication failed for {cfg.host}:{cfg.port} using {tls_mode}. "
            "Please verify SMTP_USERNAME/SMTP_PASSWORD, use an app password if required, "
            "and ensure SMTP AUTH is enabled for the account."
        ) from exc
    except smtplib.SMTPServerDisconnected as exc:
        raise RuntimeError(
            f"SMTP server disconnected unexpectedly for {cfg.host}:{cfg.port} using {tls_mode}. "
            "Port 465 must use SMTP_SSL; other ports such as 587 must use STARTTLS."
        ) from exc

    logger.info("SMTP delivery completed via %s:%s using %s", cfg.host, cfg.port, tls_mode)
