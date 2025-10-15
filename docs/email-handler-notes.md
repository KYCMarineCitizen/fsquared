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
