from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable, Sequence

from .config import SMTPSettings


class EmailClient:
    """SMTP client that enforces TLS and sender restrictions."""

    def __init__(self, settings: SMTPSettings, logger):
        self.settings = settings
        self.logger = logger

    def _validate_from_address(self, from_address: str) -> str:
        addr = from_address.strip().lower()
        if "@" not in addr:
            raise ValueError("Invalid from address supplied.")

        if addr in self.settings.allowed_from_addresses:
            return addr

        domain = addr.split("@", maxsplit=1)[1]
        if self.settings.allowed_from_domains:
            if domain not in self.settings.allowed_from_domains:
                raise ValueError(
                    f"From address '{addr}' not in allowed domains "
                    f"{sorted(self.settings.allowed_from_domains)}."
                )
            return addr

        raise ValueError(
            f"From address '{addr}' is not part of the allowed list "
            f"{sorted(self.settings.allowed_from_addresses)}."
        )

    def _validate_recipients(self, recipients: Sequence[str]) -> list[str]:
        cleansed = [recipient.strip() for recipient in recipients if recipient.strip()]
        if not cleansed:
            raise ValueError("At least one recipient must be provided.")
        return cleansed

    def send_email(
        self,
        *,
        subject: str,
        body: str,
        recipients: Sequence[str],
        reply_to: str | None = None,
        from_address: str | None = None,
        headers: Iterable[tuple[str, str]] | None = None,
    ) -> None:
        from_addr = self._validate_from_address(from_address or self.settings.default_from)
        to_addresses = self._validate_recipients(recipients)

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = from_addr
        message["To"] = ", ".join(to_addresses)
        if reply_to:
            message["Reply-To"] = reply_to.strip()
        if headers:
            for key, value in headers:
                if key.lower() not in {"subject", "from", "to", "reply-to"}:
                    message[key] = value
        message.set_content(body)

        context = ssl.create_default_context()
        if self.settings.use_ssl:
            smtp = smtplib.SMTP_SSL(
                host=self.settings.host,
                port=self.settings.port,
                context=context,
            )
        else:
            smtp = smtplib.SMTP(host=self.settings.host, port=self.settings.port)

        try:
            if not self.settings.use_ssl and self.settings.enforce_tls:
                smtp.starttls(context=context)
            smtp.login(self.settings.username, self.settings.password)
            smtp.send_message(message)
            self.logger.info(
                "Email sent | from=%s | to=%s | subject=%s",
                from_addr,
                ";".join(to_addresses),
                subject,
            )
        finally:
            smtp.quit()

