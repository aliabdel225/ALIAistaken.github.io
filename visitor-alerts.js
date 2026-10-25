(() => {
  const endpoint = window.PORTFOLIO_VISITOR_ALERT_ENDPOINT;
  if (!endpoint || !/^https:\/\/[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev\/?$/i.test(endpoint)) return;

  const sessionKey = "portfolio-visit-alert-sent";
  try {
    if (sessionStorage.getItem(sessionKey)) return;
    sessionStorage.setItem(sessionKey, "1");
  } catch {
    // Continue without session storage when browser privacy settings block it.
  }

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      page: window.location.pathname || "/",
      title: document.title
    }),
    keepalive: true
  }).catch(() => {
    // Visitor alerts must not affect the portfolio page experience.
  });
})();
