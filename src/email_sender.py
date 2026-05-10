from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import SMTPConfig


def send_email(cfg: SMTPConfig, subject: str, text_body: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.email_from
    msg["To"] = cfg.email_to

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(cfg.host, cfg.port, timeout=45) as server:
        server.starttls()
        server.login(cfg.username, cfg.password)
        server.sendmail(cfg.email_from, [cfg.email_to], msg.as_string())
