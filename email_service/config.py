from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_route_map(value: str | None) -> Dict[str, List[str]]:
    """
    Parse CONTACT_ROUTE_MAP string into a dictionary.
    Expected format (case insensitive domains):
        marinecitizen.com=support@marinecitizen.com,ops@marinecitizen.com;
        fsquared.ai=team@fsquared.ai
    """
    routes: Dict[str, List[str]] = {}
    if not value:
        return routes

    parts = [segment.strip() for segment in value.split(";") if segment.strip()]
    for segment in parts:
        if "=" not in segment:
            raise ValueError(
                f"Invalid CONTACT_ROUTE_MAP segment '{segment}'. "
                "Expected 'domain=recipient1@example.com,recipient2@example.com'."
            )
        domain, recipients = segment.split("=", maxsplit=1)
        domain_key = domain.strip().lower()
        parsed_recipients = _split_csv(recipients)
        if not parsed_recipients:
            raise ValueError(f"No recipients configured for domain '{domain_key}'.")
        routes[domain_key] = parsed_recipients
    return routes


@dataclass(slots=True)
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool
    enforce_tls: bool
    default_from: str
    allowed_from_addresses: set[str]
    allowed_from_domains: set[str]
    log_path: Path


@dataclass(slots=True)
class ServiceConfig:
    smtp: SMTPSettings
    default_recipients: List[str]
    domain_routes: Dict[str, List[str]]
    rate_limit_requests: int
    rate_limit_window_seconds: int


def _ensure_from_whitelist(default_from: str, allowed: Iterable[str]) -> set[str]:
    whitelist = {addr.lower() for addr in allowed if addr}
    if default_from.lower() not in whitelist:
        whitelist.add(default_from.lower())
    return whitelist


def load_config() -> ServiceConfig:
    """Load configuration from environment variables."""
    tls_mode = os.getenv("SMTP_TLS_MODE", "starttls").strip().lower()
    if tls_mode not in {"starttls", "ssl"}:
        raise ValueError("SMTP_TLS_MODE must be either 'starttls' or 'ssl'.")

    host = os.getenv("SMTP_HOST", "smtp-relay.gmail.com").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    default_from = os.getenv("SMTP_DEFAULT_FROM", "noreply@marinecitizen.com").strip()

    if not username or not password:
        raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be set.")

    allowed_addresses = _split_csv(os.getenv("SMTP_ALLOWED_FROM"))
    allowed_domains = {domain.lower() for domain in _split_csv(os.getenv("SMTP_ALLOWED_DOMAINS"))}

    log_path_env = os.getenv("EMAIL_LOG_PATH", "logs/email-handler.log")
    log_path = Path(log_path_env).expanduser()

    default_recipients = _split_csv(os.getenv("CONTACT_DEFAULT_RECIPIENTS"))
    route_map = _parse_route_map(os.getenv("CONTACT_ROUTE_MAP"))

    rate_limit_requests = int(os.getenv("CONTACT_RATE_LIMIT_COUNT", "10"))
    rate_limit_window_seconds = int(os.getenv("CONTACT_RATE_LIMIT_WINDOW", "60"))

    smtp_settings = SMTPSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        use_ssl=tls_mode == "ssl",
        enforce_tls=True,
        default_from=default_from.lower(),
        allowed_from_addresses=_ensure_from_whitelist(default_from, allowed_addresses),
        allowed_from_domains=allowed_domains,
        log_path=log_path,
    )

    return ServiceConfig(
        smtp=smtp_settings,
        default_recipients=default_recipients,
        domain_routes=route_map,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window_seconds=rate_limit_window_seconds,
    )

