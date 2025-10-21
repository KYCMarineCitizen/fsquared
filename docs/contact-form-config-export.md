# FSquared Contact Form Configuration Export

This note captures the configuration work required to wire the public contact form
(`contacts.html` ➜ `script.js`) to the SMTP relay-backed email service in
`email_service/`.

---

## 1. Front-End Expectations

- **Form markup**  
  `contacts.html` hosts the `<form id="quick-contact-form">`. The JavaScript helper
  (`script.js`) reads the `data-endpoint` attribute (default `/contact`) and posts a
  JSON payload when the user submits.

- **Payload contract**  
  The FastAPI handler expects the schema defined in
  `email_service/schemas.py::ContactRequest`:

  ```json
  {
    "site": "fsquared.ai",            // required: domain the user is on
    "company": "Fsquared (holding)",  // label shown to the user
    "name": "Visitor Name",           // required
    "email": "visitor@example.com",   // required
    "message": "Question...",
    "recaptchaToken": "<token>"       // optional but strongly recommended
  }
  ```

  Update `script.js` (or add hidden inputs) to send `site` and `recaptchaToken`
  alongside the existing fields. The helper already disables the submit button,
  handles errors, and surfaces the relay error message to the user.

- **reCAPTCHA / anti-bot**  
  Integrate reCAPTCHA v3 (or equivalent) on the page and ensure the client submits
  the token as `recaptchaToken`. The relay validates the token before sending.

- **CORS/Origin**  
  When deploying the service, make sure the origin that serves these pages is
  whitelisted; otherwise the fetch call will fail with a CORS error.

---

## 2. Email Relay Environment Variables

Populate the environment (Cloud Run, local `.env`, etc.) with the following keys.
See `.env.example` for the authoritative list.

| Variable | Example / Notes |
| --- | --- |
| `SMTP_HOST` | `smtp-relay.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_TLS_MODE` | `starttls` (or `ssl`) |
| `SMTP_USERNAME` | `noreply@marinecitizen.com` *(relay identity)* |
| `SMTP_PASSWORD` | App password / relay credential stored in Secret Manager |
| `SMTP_DEFAULT_FROM` | `noreply@marinecitizen.com` |
| `SMTP_ALLOWED_FROM` | Comma list of every noreply alias (`noreply@fsquared.ai`, `noreply@onlyallow.ai`, etc.) |
| `SMTP_ALLOWED_DOMAINS` | `marinecitizen.com,fsquared.ai,onlyallow.ai,quirkbot.ai,virusfor.ai,batchforge.ai` |
| `CONTACT_ROUTE_MAP` | `fsquared.ai=ops@fsquared.ai;onlyallow.ai=ops@onlyallow.ai;…` |
| `CONTACT_DEFAULT_RECIPIENTS` | Fallback recipients when the domain is missing |
| `CONTACT_RATE_LIMIT_COUNT` / `CONTACT_RATE_LIMIT_WINDOW` | Throttle repeated submissions per IP |
| `EMAIL_LOG_PATH` | `logs/email-handler.log` (or `/var/log/...` in Cloud Run) |

**Routing reminder:** `CONTACT_ROUTE_MAP` keys must be lower-case domains. The relay
lowercases and matches the `site` field from the request to this map.

---

## 3. Google Workspace SMTP Relay Checklist

1. **Admin Console → Gmail → Routing → SMTP relay service**
   - Create (or reuse) an entry such as *FSquared Contact Relay*.
   - Authentication: require SMTP auth and restrict senders to the noreply accounts.
   - Allowed senders: `Only addresses in my domains`.
   - Force TLS; add Cloud Run egress IPs if you lock on IP ranges (current allow list
     includes `34.45.61.217`).

2. **Credentials**
   - Generate an App Password (or use relay credentials) for the sending mailbox.
   - Store in Secret Manager as `contact-smtp-password`; grant Cloud Run service
     account access.
   - Record the secret name in your IaC / deployment notes.

3. **Deliverability**
   - Confirm SPF/DKIM/DMARC records exist for every alias domain (fsquared.ai,
     onlyallow.ai, quirkbot.ai, virusfor.ai, batchforge.ai).
   - Rotate DKIM keys when adding new domains and verify status in the Admin Console.

---

## 4. Deployment & Testing

- **Cloud Run / Hosting**
  - Mount `SMTP_*`, `CONTACT_*`, and logging variables via environment variables.
  - Optionally map the secrets directly using Secret Manager references.
  - Expose the FastAPI service behind HTTPS; restrict to known origins via CORS.

- **Smoke test**
  ```bash
  source .venv/bin/activate
  export $(grep -v '^#' .env | xargs)   # or set env vars in your shell
  python -m email_service.test_send \
    --site fsquared.ai \
    --company "Fsquared (holding)" \
    --reply-to you@example.com \
    --subject "Contact form relay test"
  ```

- **Front-end verification**
  - Submit the contact form in each environment.
  - Watch Cloud Run logs for the structured entry and confirm the message reaches the
    mapped mailbox.
  - Validate reCAPTCHA scores and adjust thresholds if spam leaks through.

---

### Status Summary

- ✅ SMTP relay config documented (`email-handler-notes.md`, section *Google Workspace SMTP Relay*)
- ✅ Environment variable map in `.env.example`
- ✅ Contact form markup (`contacts.html`) and client logic (`script.js`) ready to post to the relay  
- 🔧 Remaining: send `site` + `recaptchaToken` from the front-end, supply real secret values, and deploy the relay.

