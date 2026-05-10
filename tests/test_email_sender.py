import smtplib
import unittest
from dataclasses import replace
from unittest.mock import MagicMock, call, patch, sentinel

from src.config import SMTPConfig
from src.email_sender import send_email


class EmailSenderTests(unittest.TestCase):
    def setUp(self):
        self.base_cfg = SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="bot@example.com",
            password="secret",
            email_to="reader@example.com",
            email_from="bot@example.com",
        )

    @patch("src.email_sender._preflight_dns")
    @patch("src.email_sender.ssl.create_default_context", return_value=sentinel.context)
    @patch("src.email_sender.smtplib.SMTP_SSL")
    def test_send_email_uses_smtp_ssl_for_port_465(self, smtp_ssl, create_context, preflight_dns):
        cfg = replace(self.base_cfg, port=465)
        server = MagicMock()
        smtp_ssl.return_value.__enter__.return_value = server

        send_email(cfg, "Subject", "text body", "<p>html body</p>")

        preflight_dns.assert_called_once_with(cfg.host)
        create_context.assert_called_once_with()
        smtp_ssl.assert_called_once_with(
            cfg.host,
            cfg.port,
            context=sentinel.context,
            timeout=30,
        )
        server.login.assert_called_once_with(cfg.username, cfg.password)
        server.sendmail.assert_called_once()

    @patch("src.email_sender._preflight_dns")
    @patch("src.email_sender.ssl.create_default_context", return_value=sentinel.context)
    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_uses_starttls_for_non_465_ports(self, smtp_cls, create_context, preflight_dns):
        server = MagicMock()
        smtp_cls.return_value.__enter__.return_value = server

        send_email(self.base_cfg, "Subject", "text body", "<p>html body</p>")

        preflight_dns.assert_called_once_with(self.base_cfg.host)
        create_context.assert_called_once_with()
        smtp_cls.assert_called_once_with(self.base_cfg.host, self.base_cfg.port, timeout=30)
        self.assertEqual(server.ehlo.call_args_list, [call(), call()])
        server.starttls.assert_called_once_with(context=sentinel.context)
        server.login.assert_called_once_with(self.base_cfg.username, self.base_cfg.password)
        server.sendmail.assert_called_once()

    @patch("src.email_sender._preflight_dns")
    @patch("src.email_sender.ssl.create_default_context", return_value=sentinel.context)
    @patch(
        "src.email_sender.smtplib.SMTP",
        side_effect=smtplib.SMTPServerDisconnected("Connection unexpectedly closed"),
    )
    def test_send_email_wraps_disconnect_error_with_tls_guidance(
        self,
        smtp_cls,
        create_context,
        preflight_dns,
    ):
        with self.assertRaises(RuntimeError) as ctx:
            send_email(self.base_cfg, "Subject", "text body", "<p>html body</p>")

        preflight_dns.assert_called_once_with(self.base_cfg.host)
        create_context.assert_called_once_with()
        smtp_cls.assert_called_once_with(self.base_cfg.host, self.base_cfg.port, timeout=30)
        self.assertIn("smtp.example.com:587", str(ctx.exception))
        self.assertIn("STARTTLS", str(ctx.exception))

    @patch("src.email_sender._preflight_dns")
    @patch("src.email_sender.ssl.create_default_context", return_value=sentinel.context)
    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_wraps_authentication_error(self, smtp_cls, create_context, preflight_dns):
        server = MagicMock()
        server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad credentials")
        smtp_cls.return_value.__enter__.return_value = server

        with self.assertRaises(RuntimeError) as ctx:
            send_email(self.base_cfg, "Subject", "text body", "<p>html body</p>")

        preflight_dns.assert_called_once_with(self.base_cfg.host)
        create_context.assert_called_once_with()
        smtp_cls.assert_called_once_with(self.base_cfg.host, self.base_cfg.port, timeout=30)
        self.assertIn("SMTP authentication failed", str(ctx.exception))
        self.assertIn("SMTP_USERNAME/SMTP_PASSWORD", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
