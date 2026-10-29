(function () {
  const STORAGE_KEY = "sightra_cookie_choice";
  const API = "/api/privacy/cookies/";

  function getCsrf() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function readLocal() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch {
      return null;
    }
  }

  function writeLocal(optionalAccepted) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ essential: true, optional: optionalAccepted, at: new Date().toISOString() })
    );
  }

  function hideBanner() {
    const banner = document.getElementById("cookie-banner");
    if (banner) banner.hidden = true;
  }

  function showBanner() {
    const banner = document.getElementById("cookie-banner");
    if (banner) {
      banner.hidden = false;
      document.getElementById("cookie-reject")?.focus();
    }
  }

  async function save(optionalAccepted) {
    writeLocal(optionalAccepted);
    hideBanner();
    try {
      const headers = { "Content-Type": "application/json" };
      const token = getCsrf();
      if (token) headers["X-CSRFToken"] = token;
      await fetch(API, {
        method: "POST",
        credentials: "same-origin",
        headers,
        body: JSON.stringify({ optional: optionalAccepted }),
      });
    } catch {
      /* local choice still stored */
    }
    window.SightraUI?.announce(
      optionalAccepted ? "Optional cookies accepted." : "Optional cookies rejected. Essential cookies remain on."
    );
  }

  document.addEventListener("DOMContentLoaded", () => {
    const banner = document.getElementById("cookie-banner");
    if (!banner) return;
    document.getElementById("cookie-reject")?.addEventListener("click", () => save(false));
    document.getElementById("cookie-accept")?.addEventListener("click", () => save(true));

    if (readLocal()) {
      hideBanner();
      return;
    }
    showBanner();
  });
})();
