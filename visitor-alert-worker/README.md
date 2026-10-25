# Portfolio visitor email alerts

This Worker sends one alert the first time a browser session opens a portfolio page. The email contains the page path, page title, and UTC time. It does not include the visitor's IP address. A Cloudflare rate limit allows up to 10 requests per IP per minute.

## Requirements

- A Cloudflare Worker named `portfolio-visitor-alert` already created in your account.
- A Cloudflare API token with Editor access scoped to that Worker.
- A Resend API key with sending access.
- The recipient email stored as the `ALERT_TO` Worker secret. For Resend's test sender, this must match the email registered to your Resend account.

The portfolio repository is public. Never put either API key or the recipient address in source code or commit them.

## Deploy from Linux

From the repository root:

```bash
cd visitor-alert-worker
```

Create a Cloudflare user API token in **My Profile > API Tokens**. Give it **Workers Editor** access scoped to the existing `portfolio-visitor-alert` Worker only. Cloudflare's `wrangler login` OAuth flow asks for broad permissions; this scoped token avoids access to unrelated account services.

Get your Cloudflare Account ID from the account overview. In the terminal, enter the token without echoing it, set the account ID, then deploy:

```bash
read -rsp "Cloudflare API token: " CLOUDFLARE_API_TOKEN; printf '\n'
export CLOUDFLARE_API_TOKEN
export CLOUDFLARE_ACCOUNT_ID="PASTE_YOUR_ACCOUNT_ID"
npx wrangler@latest deploy
```

Wrangler will print the Worker URL, similar to `https://portfolio-visitor-alert.<your-subdomain>.workers.dev`.

Add the two private Worker secrets. Wrangler prompts for their values:

```bash
npx wrangler@latest secret put RESEND_API_KEY
npx wrangler@latest secret put ALERT_TO
unset CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
```

Enter the Resend API key for the first secret and the email registered to Resend for the second. Do not share either value in chat or GitHub.

## Connect the portfolio

Send the Worker URL to me. I will place it in `visitor-alert-config.js` and update the portfolio.

The Worker currently accepts requests only from `https://aliabdel225.github.io`. If your site uses another domain, update `ALLOWED_ORIGIN` in `wrangler.jsonc` to the site's origin (scheme and hostname only), then deploy again.

## Disable alerts

Clear `window.PORTFOLIO_VISITOR_ALERT_ENDPOINT` in `visitor-alert-config.js`, or disable the Worker in Cloudflare.
