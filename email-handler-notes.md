# Email Handler Setup Notes

## High-Level Architecture
- Front-end contact form posts to a secure HTTPS endpoint (preferably on Cloud Run).
- Cloud Run handler validates payload, performs reCAPTCHA check, and sends email through a trusted provider (Google Workspace via Gmail API or transactional service).
- Secrets (API keys, OAuth credentials) live in Secret Manager; handler retrieves them at runtime.
- Logging goes to Cloud Logging for auditing; optional Pub/Sub for additional processing.

## Operational Steps
1. **Email Sender**
   - Provision dedicated sender addresses such as `noreply@fsquared.ai`.
   - Generate credentials (OAuth for Gmail API or API key for SendGrid/Mailgun/Postmark).
   - Store credentials in Secret Manager and grant Cloud Run’s service account `Secret Manager Secret Accessor`.

2. **Service Implementation**
   - Create a small web service (Node, Python, Go, etc.) with an endpoint that:
     - Accepts POST `{ company, name, email, message, recaptchaToken }`.
     - Verifies reCAPTCHA server-side.
     - Validates input and sanitizes content.
     - Sends email via chosen provider using dedicated sender.
     - Sets `Reply-To` to the customer email so replies reach the customer.
     - Logs structured events; returns only generic responses to clients.

3. **Cloud Run Deployment**
   - Containerize the service and deploy to Cloud Run.
   - Attach secrets as environment variables.
   - Optionally restrict invokers and front with Cloud Armor if higher security is needed.

4. **DNS / Deliverability**
   - Configure SPF, DKIM, DMARC records for each domain in Google Domains.
   - Use Workspace tools (or provider tools) to generate DKIM keys per alias domain.
   - Test deliverability using Gmail/Postmark diagnostics.

5. **Front-End Integration**
   - Update the website form to call the Cloud Run endpoint via `fetch`.
   - Include reCAPTCHA token and any anti-bot measures (honeypot field).
   - Handle success/failure responses gracefully in the UI.

## Multiple Domains
- One Cloud Run service can handle all domains: map `company` to `{ fromAddress, toAddress }`.
- Ensure the service account or API key is authorized to send as each alias (e.g., `noreply@onlyallow.ai`, `noreply@batchforge.ai`).
- Maintain per-domain DNS records (SPF/DKIM/DMARC) for deliverability.

## Alias Domains
- Workspace supports alias domains; create the sender mailbox or alias (`noreply@fsquared.ai`) under the primary tenant.
- Authenticate via Gmail API or provider using that alias; ensure DNS entries exist for the alias domain.

## Security Checklist
- reCAPTCHA v3 (or hCaptcha) verification.
- Strict CORS (allow only your site origins) and optional Cloud Armor rate limiting.
- Secrets in Secret Manager, rotated periodically.
- Logging and monitoring for anomalies; set alerting on error spikes.

## Google Workspace SMTP Relay Configuration
- In Google Admin Console, open `Apps > Google Workspace > Gmail > Routing > SMTP relay service` and create an entry named `FSquared Contact Relay`.
- Authentication: require SMTP authentication and restrict senders to the noreply accounts (add `noreply@marinecitizen.com`, `noreply@fsquared.ai`, plus future aliases).
- Allowed senders: set to `Only addresses in my domains`; enable forced TLS.
- Client access: allow the public IP `34.45.61.217` even though SMTP auth is enabled (keeps parity with Google’s best practice).
- Generate an app password for `noreply@marinecitizen.com` (Account > Security > App passwords) to use as `SMTP_PASSWORD` and store in Secret Manager (`projects/fsquared/secrets/contact-smtp-password`).
- Repeat DKIM enablement for future alias domains before pointing traffic at them.

## Contact Service (FastAPI)
- New code lives in `email_service/` with a FastAPI app that wraps the SMTP relay.
- Configuration is drawn from environment variables (see `.env.example`). Critical ones:
  - `SMTP_HOST=smtp-relay.gmail.com`, `SMTP_PORT=587`, `SMTP_TLS_MODE=starttls`.
  - `SMTP_USERNAME=noreply@marinecitizen.com`, `SMTP_PASSWORD=<app password>`.
  - `SMTP_ALLOWED_FROM` and `SMTP_ALLOWED_DOMAINS` list all noreply senders across domains.
  - `CONTACT_ROUTE_MAP` maps site domains to internal recipients.
  - `EMAIL_LOG_PATH` controls where structured logs go (`logs/email-handler.log` by default).
- Rate limiting is in-memory (configurable via `CONTACT_RATE_LIMIT_*`). For Cloud Run, move to Redis/Memorystore later if needed.

### Local Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r email_service/requirements.txt
cp .env.example .env  # update secrets (never commit the real file)
uvicorn email_service.app:app --reload
```

- Endpoint `POST /contact` accepts the payload defined in `email_service/schemas.py`.
- Health probe at `/healthz`.

### CLI Smoke Test
```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)  # or use python-dotenv
python -m email_service.test_send \
  --site marinecitizen.com \
  --reply-to tester@example.com \
  --subject "Workspace Relay Test"
```

- Adjust `--to` for ad-hoc recipients; omit to use the routing map.
- Logs accumulate under `logs/email-handler.log` with timestamp, request metadata, and delivery result.

### Deployment Notes
- Mount secrets in Cloud Run as environment variables (`SMTP_USERNAME`, `SMTP_PASSWORD`).
- Configure `EMAIL_LOG_PATH` to `/var/log/email-handler.log`; use Cloud Logging sidecar or direct stdout if preferred.
- Add Google-managed certificates/DNS for additional aliases prior to enabling them in `SMTP_ALLOWED_DOMAINS`.
- Enable Cloud Armor or FastAPI middleware for Geo/IP filters if form spam increases.
