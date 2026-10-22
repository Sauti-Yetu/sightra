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

  function initPasswordToggles() {
    document.querySelectorAll("[data-password-target]").forEach((btn) => {
      const id = btn.getAttribute("data-password-target");
      const input = document.getElementById(id);
      if (!input) return;
      btn.addEventListener("click", () => {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
        const icon = btn.querySelector(".material-symbols-outlined");
        if (icon) icon.textContent = show ? "visibility_off" : "visibility";
      });
    });
  }

  function isStandalonePwa() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  function detectInstallPlatform() {
    const ua = navigator.userAgent;
    const isIOS =
      /iPad|iPhone|iPod/.test(ua) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const isAndroid = /Android/i.test(ua);
    if (isIOS) return "ios";
    if (isAndroid) return "android";
    return "other";
  }

  const SightraPWA = (function () {
    let deferredPrompt = null;
    const platform = detectInstallPlatform();

    function canInstall() {
      if (isStandalonePwa()) return false;
      if (deferredPrompt) return true;
      if (platform === "ios") return true;
      if (platform === "android" && "serviceWorker" in navigator) return true;
      return !!deferredPrompt;
    }

    function setInstallButtonsVisible(show) {
      document.querySelectorAll("[data-pwa-install]").forEach((el) => {
        if (isStandalonePwa()) {
          el.hidden = true;
          el.setAttribute("aria-hidden", "true");
          return;
        }
        el.hidden = !show;
        el.removeAttribute("aria-hidden");
      });
    }

    function fillModal(mode) {
      const lead = document.getElementById("pwa-install-modal-lead");
      const steps = document.getElementById("pwa-install-modal-steps");
      const action = document.getElementById("pwa-install-modal-action");
      if (!lead || !steps || !action) return;

      steps.innerHTML = "";
      if (mode === "android-native") {
        lead.textContent =
          "Install Sightra like a regular app. It opens full screen and loads faster on your home screen.";
        action.textContent = "Install now";
        action.hidden = false;
        return;
      }
      if (mode === "ios") {
        lead.textContent = "On iPhone and iPad, install Sightra from Safari:";
        [
          "Open this page in Safari (not an in-app browser).",
          "Tap the Share button at the bottom of the screen.",
          "Scroll and tap “Add to Home Screen”, then tap Add.",
        ].forEach((text) => {
          const li = document.createElement("li");
          li.className = "flex gap-2";
          li.innerHTML =
            '<span class="material-symbols-outlined text-[var(--brand-cyan)] text-base">arrow_right</span><span>' +
            text +
            "</span>";
          steps.appendChild(li);
        });
        action.textContent = "Got it";
        action.hidden = false;
        return;
      }
      lead.textContent =
        "Use your browser menu and choose “Install app” or “Add to Home screen” to download Sightra.";
      [
        "Look for Install / Add to Home screen in the browser menu (⋮ or ⋯).",
        "Confirm when prompted to add Sightra to your device.",
      ].forEach((text) => {
        const li = document.createElement("li");
        li.className = "flex gap-2";
        li.innerHTML =
          '<span class="material-symbols-outlined text-[var(--brand-cyan)] text-base">arrow_right</span><span>' +
          text +
          "</span>";
        steps.appendChild(li);
      });
      action.textContent = "Got it";
      action.hidden = false;
    }

    function closeModal() {
      const modal = document.getElementById("pwa-install-modal");
      if (modal) modal.hidden = true;
    }

    function openModal(mode) {
      const modal = document.getElementById("pwa-install-modal");
      if (!modal) return;
      fillModal(mode);
      modal.hidden = false;
      announce("Install Sightra instructions opened");
    }

    async function triggerInstall() {
      if (isStandalonePwa()) {
        announce("Sightra is already installed");
        return;
      }
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const choice = await deferredPrompt.userChoice;
        deferredPrompt = null;
        if (choice.outcome === "accepted") {
          announce("Sightra installed");
          hideBanner();
          setInstallButtonsVisible(false);
        }
        closeModal();
        return;
      }
      if (platform === "ios") {
        openModal("ios");
        return;
      }
      if (platform === "android") {
        openModal(deferredPrompt ? "android-native" : "android-fallback");
        return;
      }
      openModal("other");
    }

    function hideBanner() {
      const banner = document.getElementById("pwa-install");
      if (banner) banner.hidden = true;
      try {
        sessionStorage.setItem("sightra_pwa_banner_dismissed", "1");
      } catch {
        /* ignore */
      }
    }

    function showBanner() {
      const banner = document.getElementById("pwa-install");
      const hint = banner?.querySelector("p.text-xs");
      const btn = document.getElementById("pwa-install-btn");
      if (!banner || !btn) return;
      banner.hidden = false;
      if (hint) {
        hint.textContent =
          platform === "ios"
            ? "Add Sightra to your home screen for quick access."
            : "Download Sightra to your home screen for offline-ready access.";
      }
      btn.textContent = platform === "ios" ? "How to install" : "Install app";
    }

    function bindUi() {
      document.querySelectorAll("[data-pwa-install]").forEach((el) => {
        el.addEventListener("click", (e) => {
          e.preventDefault();
          triggerInstall();
        });
      });

      const bannerBtn = document.getElementById("pwa-install-btn");
      if (bannerBtn) bannerBtn.addEventListener("click", () => triggerInstall());

      const closeBtn = document.getElementById("pwa-install-modal-close");
      const dismissBtn = document.getElementById("pwa-install-modal-dismiss");
      const backdrop = document.getElementById("pwa-install-modal-backdrop");
      const actionBtn = document.getElementById("pwa-install-modal-action");
      const bannerDismiss = document.getElementById("pwa-install-dismiss");
      [closeBtn, dismissBtn].forEach((btn) => {
        if (btn) btn.addEventListener("click", closeModal);
      });
      if (backdrop) backdrop.addEventListener("click", closeModal);
      if (bannerDismiss) bannerDismiss.addEventListener("click", hideBanner);
      if (actionBtn) {
        actionBtn.addEventListener("click", () => {
          if (deferredPrompt) triggerInstall();
          else closeModal();
        });
      }
    }

    function init() {
      if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
          navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
        });
      }

      bindUi();

      if (isStandalonePwa()) {
        setInstallButtonsVisible(false);
        return;
      }

      setInstallButtonsVisible(true);

      window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredPrompt = e;
        showBanner();
        setInstallButtonsVisible(true);
        fillModal("android-native");
      });

      window.addEventListener("appinstalled", () => {
        deferredPrompt = null;
        hideBanner();
        setInstallButtonsVisible(false);
        announce("Sightra installed on your device");
      });

      try {
        const dismissed = sessionStorage.getItem("sightra_pwa_banner_dismissed");
        if (platform === "ios" && !dismissed) {
          window.setTimeout(() => {
            if (!deferredPrompt) showBanner();
          }, 2500);
        }
      } catch {
        /* sessionStorage unavailable */
      }
    }

    return { init, triggerInstall, canInstall, isStandalone: isStandalonePwa };
  })();

  function initInstallPrompt() {
    SightraPWA.init();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initA11yPanel();
    initNav();
    initPasswordToggles();
    initInstallPrompt();
  });

  window.SightraUI = { announce, applyTheme, speak };
  window.SightraPWA = SightraPWA;
})();
