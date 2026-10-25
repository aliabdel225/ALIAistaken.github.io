# Portfolio visitor email alerts

This Cloudflare Worker sends one email when a browser session first opens a portfolio page. It sends the page path, page title, and UTC time. It does not include or store the visitor's IP address. A Cloudflare rate limit allows up to 10 alert requests per IP per minute.

## Requirements

- A Cloudflare account
- A Resend account registered with the same email used in `ALERT_TO`
- The Resend API key stored as a Cloudflare Worker secret

Resend's `onboarding@resend.dev` test sender can only deliver to the email registered to the Resend account. The repository is public, so never put the API key in source code or commit it.

## Deploy

From the portfolio repository's root directory:

```bash
cd visitor-alert-worker
npx wrangler@latest login
npx wrangler@latest deploy
npx wrangler@latest secret put RESEND_API_KEY
npx wrangler@latest secret put ALERT_TO
```

When prompted, enter the Resend API key for the first secret and the destination email address for the second. Do not paste either secret into GitHub or chat. Wrangler deploys them privately to Cloudflare.

The initial deployment prints a URL similar to `https://portfolio-visitor-alert.<your-subdomain>.workers.dev`.

## Connect the portfolio

1. Open `visitor-alert-config.js` in the repository.
2. Set `window.PORTFOLIO_VISITOR_ALERT_ENDPOINT` to the Worker URL.
3. Commit and push that change to GitHub.
4. Open the live portfolio in a private window and check that the alert arrives.

The Worker allows requests only from `https://aliabdel225.github.io`. If the live portfolio uses a different domain, update `ALLOWED_ORIGIN` in `wrangler.jsonc` to that site's origin (scheme and hostname only), then deploy again.

## Disable alerts

Clear `window.PORTFOLIO_VISITOR_ALERT_ENDPOINT` in `visitor-alert-config.js`, or delete/disable the Worker in Cloudflare.

