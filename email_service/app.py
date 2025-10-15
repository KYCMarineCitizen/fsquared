from __future__ import annotations

import time
import logging
from collections import defaultdict, deque
from typing import Deque, Dict, List

from fastapi import FastAPI, HTTPException, Request, status

from .config import ServiceConfig, load_config
from .email_client import EmailClient
from .logging_utils import configure_logging
from .schemas import ContactRequest, ContactResponse

app = FastAPI(title="FSquared Contact Service", version="1.0.0")

service_config: ServiceConfig | None = None
logger: logging.Logger | None = None
email_client: EmailClient | None = None
rate_limiter: SlidingWindowRateLimiter | None = None


class SlidingWindowRateLimiter:
    """In-memory rate limiter for low-volume endpoints."""

    def __init__(self, *, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again shortly.",
            )
        bucket.append(now)


def _select_recipients(payload: ContactRequest, config: ServiceConfig) -> List[str]:
    site_key = payload.site.strip().lower()
    if site_key in config.domain_routes:
        return config.domain_routes[site_key]
    if config.default_recipients:
        return config.default_recipients
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"No contact route configured for site '{payload.site}'.",
    )


@app.on_event("startup")
def startup_event() -> None:
    global service_config, logger, email_client, rate_limiter
    service_config = load_config()
    logger = configure_logging(service_config.smtp.log_path)
    email_client = EmailClient(service_config.smtp, logger)
    rate_limiter = SlidingWindowRateLimiter(
        limit=service_config.rate_limit_requests,
        window_seconds=service_config.rate_limit_window_seconds,
    )
    logger.info("Contact service initialised. Allowed domains: %s", sorted(
        service_config.smtp.allowed_from_domains or service_config.smtp.allowed_from_addresses
    ))


@app.post("/contact", response_model=ContactResponse)
async def handle_contact(request: Request, payload: ContactRequest) -> ContactResponse:
    if not all([service_config, email_client, rate_limiter]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready. Please retry shortly.",
        )

    config = service_config
    client = email_client
    limiter = rate_limiter

    assert config is not None
    assert client is not None
    assert limiter is not None

    client_ip = request.client.host if request.client else "unknown"
    limiter.hit(client_ip)

    recipients = _select_recipients(payload, config)
    subject = f"[{payload.site}] Contact form submission from {payload.name}"

    body_lines = [
        f"Company: {payload.company}",
        f"Name: {payload.name}",
        f"Email: {payload.email}",
        "",
        payload.message,
    ]
    body = "\n".join(body_lines)

    client.send_email(
        subject=subject,
        body=body,
        recipients=recipients,
        reply_to=payload.email,
    )

    if logger:
        logger.info(
            "Contact request processed | site=%s | company=%s | ip=%s",
            payload.site,
            payload.company,
            client_ip,
        )

    return ContactResponse(success=True, message="Request submitted.")


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
