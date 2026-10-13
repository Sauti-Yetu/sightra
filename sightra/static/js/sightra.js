(function () {
  const STORAGE_THEME = "sightra_theme";
  const STORAGE_A11Y = "sightra_a11y";

  function readA11y() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_A11Y) || "{}");
    } catch {
      return {};
    }
  }

  function writeA11y(data) {
    localStorage.setItem(STORAGE_A11Y, JSON.stringify(data));
  }

  function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem(STORAGE_THEME, theme);
    const icon = document.getElementById("theme-toggle-icon");
    if (icon) icon.textContent = isDark ? "light_mode" : "dark_mode";
    window.dispatchEvent(new CustomEvent("sightra:theme", { detail: { theme } }));
  }

  function applyA11y(opts) {
    const root = document.documentElement;
    root.toggleAttribute("data-a11y-contrast", opts.highContrast === true);
    if (opts.highContrast) root.setAttribute("data-a11y-contrast", "high");
    else root.removeAttribute("data-a11y-contrast");

    if (opts.reduceMotion) root.setAttribute("data-a11y-motion", "reduce");
    else root.removeAttribute("data-a11y-motion");

    root.toggleAttribute("data-a11y-voice", opts.voiceFeedback === true);
    writeA11y(opts);
    syncPreferences({ accessibility: opts });
  }

  function speak(text) {
    const a11y = readA11y();
    if (!a11y.voiceFeedback || !window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1;
    window.speechSynthesis.speak(utter);
  }

  function announce(message) {
    const live = document.getElementById("sr-live");
    if (live) live.textContent = message;
    speak(message);
  }

  async function syncPreferences(partial) {
    try {
      await fetch("/api/accounts/preferences/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrf() },
        credentials: "same-origin",
        body: JSON.stringify(partial),
      });
    } catch {
      /* optional when logged out */
    }
  }

  function getCsrf() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function initTheme() {
    const saved = localStorage.getItem(STORAGE_THEME) || localStorage.getItem("theme") || "dark";
    applyTheme(saved);
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", () => {
        const next = document.documentElement.classList.contains("dark") ? "light" : "dark";
        applyTheme(next);
        syncPreferences({ theme: next });
        announce(next === "dark" ? "Dark mode enabled" : "Light mode enabled");
      });
    }
  }

  function initA11yPanel() {
    const panel = document.getElementById("a11y-panel");
    const toggle = document.getElementById("a11y-toggle");
    if (!panel || !toggle) return;

    const opts = Object.assign(
      { highContrast: false, reduceMotion: false, voiceFeedback: false, largeText: false },
      readA11y()
    );
    applyA11y(opts);

    toggle.addEventListener("click", () => {
      const hidden = panel.hasAttribute("hidden");
      if (hidden) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "hidden");
      announce(hidden ? "Accessibility options opened" : "Accessibility options closed");
    });

    panel.querySelectorAll("[data-a11y-key]").forEach((input) => {
      const key = input.getAttribute("data-a11y-key");
      input.checked = !!opts[key];
      input.addEventListener("change", () => {
        opts[key] = input.checked;
        if (key === "largeText") {
          document.documentElement.style.fontSize = input.checked ? "106%" : "";
        }
        applyA11y(opts);
        announce(`${key} ${input.checked ? "enabled" : "disabled"}`);
      });
    });
  }

  function initNav() {
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    document.querySelectorAll("[data-nav-target], .sidebar-link[data-nav-target]").forEach((link) => {
      const target = link.getAttribute("data-nav-target");
      const normalized = target === "/" ? "/" : target.replace(/\/$/, "");
      const active =
        path === normalized || (normalized !== "/" && path.startsWith(normalized));
      if (active) link.classList.add("is-active");
    });
  }

  function initInstallPrompt() {
    if (!("serviceWorker" in navigator)) return;
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });

    let deferred;
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      deferred = e;
      const banner = document.getElementById("pwa-install");
      if (banner) banner.hidden = false;
    });

    const btn = document.getElementById("pwa-install-btn");
    if (btn) {
      btn.addEventListener("click", async () => {
        if (!deferred) return;
        deferred.prompt();
        await deferred.userChoice;
        deferred = null;
        const banner = document.getElementById("pwa-install");
        if (banner) banner.hidden = true;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initA11yPanel();
    initNav();
    initInstallPrompt();
  });

  window.SightraUI = { announce, applyTheme, speak };
})();
