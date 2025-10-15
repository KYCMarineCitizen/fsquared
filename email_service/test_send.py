from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
from typing import List

from .config import load_config
from .email_client import EmailClient
from .logging_utils import configure_logging


def _resolve_recipients(site: str | None, explicit: List[str], default: List[str], routes: dict[str, List[str]]) -> List[str]:
    if explicit:
        return explicit
    if site:
        key = site.strip().lower()
        if key in routes:
            return routes[key]
    if default:
        return default
    raise SystemExit("No recipients resolved. Provide --to or set CONTACT_DEFAULT_RECIPIENTS / CONTACT_ROUTE_MAP.")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a test email through the configured SMTP relay.")
    parser.add_argument("--site", help="Domain key to resolve recipients from CONTACT_ROUTE_MAP (e.g. marinecitizen.com).")
    parser.add_argument("--to", nargs="+", default=[], help="Override recipients for the test message.")
    parser.add_argument("--reply-to", required=True, help="Reply-To address used for the test message.")
    parser.add_argument("--subject", default=None, help="Subject line for the test message.")
    parser.add_argument("--message", default=None, help="Inline message body. Optional when using --site.")
    parser.add_argument(
        "--from-address",
        dest="from_address",
        default=None,
        help="Override configured SMTP_DEFAULT_FROM address.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = load_config()
    logger = configure_logging(config.smtp.log_path)
    client = EmailClient(config.smtp, logger)

    recipients = _resolve_recipients(args.site, args.to, config.default_recipients, config.domain_routes)

    subject = args.subject or f"SMTP Relay Smoke Test {datetime.now(timezone.utc).isoformat(timespec='seconds')}"
    body = args.message or (
        "This is an automated SMTP relay smoke test.\n\n"
        f"Sent via domain key: {args.site or 'N/A'}\n"
        "If you received this, the relay is working as expected."
    )

    client.send_email(
        subject=subject,
        body=body,
        recipients=recipients,
        reply_to=args.reply_to,
        from_address=args.from_address,
    )

    logger.info("Test message queued successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

