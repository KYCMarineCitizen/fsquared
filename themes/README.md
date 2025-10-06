Quirkbot, Onlyallow, Batchforge theme guidance

This folder contains per-company theme CSS files that override or extend the base site styles in `styles.css`.

Goal
- Keep a shared base in `styles.css` and load company CSS after it.
- Scope company rules to the page using an HTML or body class, for example:
  - <html class="onlyallow"> or <body class="onlyallow">
  - Then in the theme you can scope rules under `body.onlyallow { ... }` or `body.onlyallow .hero { ... }`.

Files
- onlyallow.css — Theme for onlyallow.ai (provided by user).
- onlyallow-interactivity.css — Interactivity overrides for onlyallow.
- quirkbot.css — Theme for quirkbot.ai (provided and integrated).
- virsfor.css — Placeholder for virsfor.ai; replace when you have styles.
- batchforge.css — Theme for batchforge.ai (Batchdrone stylesheet substituted by user).

Recommended variables to override
- The base `styles.css` includes a small set of CSS variables. When writing a theme, prefer to override these variables near the top of the theme file:

  :root {
    --brand-bg: #0f172a;       /* page background */
    --brand-fg: #e2e8f0;       /* body text color */
    --accent: #06b6d4;        /* primary accent color */
    --muted: #94a3b8;         /* muted text */
    --glass: rgba(255,255,255,0.06); /* glass/overlay */
    --glass-strong: rgba(255,255,255,0.08);
  }

- Example (in a theme file):

  body.onlyallow {
    --brand-bg: #050816;
    --brand-fg: #f7f7fb;
    --accent: #00c2a8;
  }

How to add a new company theme
1. Create a new file in this folder named after the company, e.g. `themes/myco.css`.
2. Scope rules under `body.myco` or `html.myco` to avoid leaking styles.
3. Add a link tag to the company page after the base `styles.css` link:
   <link rel="stylesheet" href="styles.css">
   <link rel="stylesheet" href="themes/myco.css">
4. Add the `class` to the top-level HTML element on that page: `<html class="myco">`.
5. Test mobile and desktop for color contrast and spacing.

Notes
- Keep selectors specific but not overly specific (prefer `body.myco .hero` over `html.onlyallow body .hero`).
- If you need to override third-party components, use more specific selectors or CSS custom properties.
- To change interactivity (hover / focus states), consider putting those in a separate `-interactivity.css` file so they can be loaded only where needed.

Contact
- If you want me to integrate additional theme files you upload, I'll replace the placeholder file and verify the company page references it.