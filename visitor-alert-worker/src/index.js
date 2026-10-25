const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };

function response(body, status, origin) {
  const headers = new Headers(JSON_HEADERS);
  if (origin) {
    headers.set("Access-Control-Allow-Origin", origin);
    headers.set("Access-Control-Allow-Methods", "POST, OPTIONS");
    headers.set("Access-Control-Allow-Headers", "Content-Type");
    headers.set("Vary", "Origin");
  }
  return new Response(body ? JSON.stringify(body) : null, { status, headers });
}

function cleanText(value, maxLength) {
  return String(value || "").replace(/[<>\u0000-\u001f\u007f]/g, "").slice(0, maxLength);
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin");
    const allowedOrigin = env.ALLOWED_ORIGIN;

    if (!allowedOrigin || origin !== allowedOrigin) {
      return new Response("Forbidden", { status: 403 });
    }

    if (request.method === "OPTIONS") {
      return response(null, 204, origin);
    }

    if (request.method !== "POST") {
      return response({ error: "Method not allowed" }, 405, origin);
    }

    const sourceIp = request.headers.get("CF-Connecting-IP") || "unknown";
    const { success } = await env.RATE_LIMITER.limit({ key: sourceIp });
    if (!success) {
      return response({ error: "Rate limit exceeded" }, 429, origin);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return response({ error: "Invalid JSON" }, 400, origin);
    }

    const page = cleanText(payload.page, 180);
    const title = cleanText(payload.title, 120);
    if (!page.startsWith("/")) {
      return response({ error: "Invalid page path" }, 400, origin);
    }

    const visitedAt = new Date().toISOString();
    const email = {
      from: "Portfolio alerts <onboarding@resend.dev>",
      to: [env.ALERT_TO],
      subject: "New visit to your cybersecurity portfolio",
      text: [
        "A visitor opened your portfolio.",
        "",
        `Page: ${page}`,
        title ? `Title: ${title}` : "",
        `Time (UTC): ${visitedAt}`,
        "",
        "This alert does not include the visitor's IP address."
      ].filter(Boolean).join("\n")
    };

    let sendResult;
    try {
      sendResult = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(email)
      });
    } catch {
      return response({ error: "Email service unavailable" }, 502, origin);
    }

    if (!sendResult.ok) {
      return response({ error: "Email delivery failed" }, 502, origin);
    }

    return response({ ok: true }, 200, origin);
  }
};
