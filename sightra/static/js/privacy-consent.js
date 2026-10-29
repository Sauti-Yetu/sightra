(function () {
  const API_STATUS = "/api/privacy/status/";
  const API_ONBOARD = "/api/privacy/onboarding/";
  const API_CONSENT = "/api/privacy/consent/";

  function getCsrf() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function ensureCsrfCookie() {
    if (getCsrf()) return;
    await fetch(API_STATUS, { credentials: "same-origin" });
  }

  async function fetchStatus() {
    await ensureCsrfCookie();
    const res = await fetch(API_STATUS, { credentials: "same-origin" });
    if (!res.ok) throw new Error("Could not load privacy status.");
    return res.json();
  }

  async function postJson(url, body) {
    await ensureCsrfCookie();
    const headers = { "Content-Type": "application/json" };
    const token = getCsrf();
    if (token) headers["X-CSRFToken"] = token;

    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify(body),
    });
    let data = {};
    try {
      data = await res.json();
    } catch {
      data = {};
    }
    if (!res.ok) {
      const msg =
        data.error ||
        (res.status === 403 ? "Security check failed. Refresh the page and try again." : "request failed");
      throw new Error(msg);
    }
    return data;
  }

  function showOnboardingModal() {
    const modal = document.getElementById("privacy-onboarding-modal");
    if (modal) modal.removeAttribute("hidden");
    window.SightraUI?.announce("Privacy choices required. Dialog opened.");
  }

  function hideOnboardingModal() {
    const modal = document.getElementById("privacy-onboarding-modal");
    if (modal) modal.setAttribute("hidden", "hidden");
  }

  async function ensureOnboarding() {
    try {
      const status = await fetchStatus();
      if (status.requires_onboarding) {
        showOnboardingModal();
        return false;
      }
      return true;
    } catch {
      return true;
    }
  }

  async function requireFeatureConsent(category, promptMessage) {
    const ok = await ensureOnboarding();
    if (!ok) return false;
    const status = await fetchStatus();
    if (status.decisions && status.decisions[category] === "granted") {
      return true;
    }
    const accept = window.confirm(
      promptMessage ||
        "Sightra needs your consent for this feature. Open Privacy settings to review?"
    );
    if (!accept) return false;
    try {
      await postJson(API_CONSENT, { category, decision: "granted", policy_slug: "privacy-policy" });
      return true;
    } catch {
      window.location.href = "/settings/privacy/";
      return false;
    }
  }

  function bindOnboardingForm() {
    const form = document.getElementById("privacy-onboarding-form");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const privacyAck = document.getElementById("po-privacy-ack");
      const coreAccept = document.getElementById("po-core-accept");
      if (!privacyAck?.checked || !coreAccept?.checked) {
        window.SightraUI?.announce("Please confirm required privacy items.");
        return;
      }
      const ageAdult = document.getElementById("po-age-adult")?.checked === true;
      const parental = document.getElementById("po-parental")?.checked === true;
      const guardianEmail = document.getElementById("po-guardian-email")?.value?.trim() || "";
      if (!ageAdult && !parental) {
        window.SightraUI?.announce("Confirm you are 18 or older, or that a parent or guardian consents.");
        return;
      }
      if (parental && !ageAdult && !guardianEmail.includes("@")) {
        window.SightraUI?.announce("Enter a parent or guardian email.");
        return;
      }
      const payload = {
        privacy_notice_ack: true,
        core_service_accept: true,
        age_adult: ageAdult,
        parental_consent: parental,
        guardian_email: guardianEmail,
        optional_history: document.getElementById("po-opt-history")?.checked === true,
        research_feedback: document.getElementById("po-opt-research")?.checked === true,
        ai_training: document.getElementById("po-opt-ai-train")?.checked === true,
        analytics: document.getElementById("po-opt-analytics")?.checked === true,
        marketing_email: document.getElementById("po-opt-marketing")?.checked === true,
      };
      const btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
      try {
        await postJson(API_ONBOARD, payload);
        hideOnboardingModal();
        window.SightraUI?.announce("Privacy choices saved.");
        window.dispatchEvent(new CustomEvent("sightra:privacy-onboarded"));
      } catch (err) {
        alert(err.message || "Could not save privacy choices.");
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  function bindPrivacySettingsForm() {
    const form = document.getElementById("privacy-settings-form");
    if (!form) return;
    form.querySelectorAll("[data-consent-category]").forEach((input) => {
      input.addEventListener("change", async () => {
        const category = input.getAttribute("data-consent-category");
        if (input.dataset.withdraw === "true" && !input.checked) {
          try {
            await postJson(API_CONSENT, { category, decision: "withdrawn", policy_slug: "privacy-policy" });
          } catch {
            input.checked = !input.checked;
          }
          return;
        }
        try {
          await postJson(API_CONSENT, {
            category,
            decision: input.checked ? "granted" : "denied",
            policy_slug: "privacy-policy",
          });
        } catch {
          input.checked = !input.checked;
        }
      });
    });
  }

  function skipOnboardingForPath() {
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    return (
      path === "/" ||
      path === "/signin" ||
      path === "/signup" ||
      path.startsWith("/legal") ||
      path === "/unsubscribe"
    );
  }

  function bindGuardianToggle() {
    const adult = document.getElementById("po-age-adult");
    const parental = document.getElementById("po-parental");
    const wrap = document.getElementById("po-guardian-wrap");
    function sync() {
      if (wrap) wrap.hidden = !(parental?.checked && !adult?.checked);
    }
    adult?.addEventListener("change", sync);
    parental?.addEventListener("change", sync);
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindOnboardingForm();
    bindPrivacySettingsForm();
    bindGuardianToggle();
    if (skipOnboardingForPath()) return;
    fetchStatus()
      .then((s) => {
        if (s.requires_onboarding && document.getElementById("privacy-onboarding-modal")) {
          showOnboardingModal();
        }
      })
      .catch(() => {});
  });

  window.SightraPrivacy = {
    ensureOnboarding,
    requireFeatureConsent,
    fetchStatus,
    CONSENT_CAMERA: "camera_environmental_analysis",
    CONSENT_MIC: "microphone_voice_input",
    CONSENT_LOCATION: "location_navigation",
  };
})();
