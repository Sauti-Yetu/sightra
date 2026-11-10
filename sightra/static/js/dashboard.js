(function () {
  const LANG = {
    en: "English",
    sw: "Swahili",
    fr: "French",
    ar: "Arabic",
    so: "Somali",
    ki: "Kikuyu",
  };

  function readA11y() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}");
    } catch {
      return {};
    }
  }

  function firstName(raw) {
    return String(raw || "").trim().split(/\s+/)[0] || "";
  }

  function fillGreeting() {
    const el = document.getElementById("greeting");
    if (!el) return;
    const name = firstName(el.getAttribute("data-display-name"));
    const rendered = el.getAttribute("data-rendered");
    const next = name ? `Welcome back, ${name}` : "Welcome back";
    // Log for debugging: ensure each user sees their own name
    if (rendered) {
      console.debug(`Dashboard rendered at ${new Date(parseInt(rendered) * 1000).toISOString()} for user: ${name || '(anonymous)'}`);
    }
    if (el.textContent !== next) el.textContent = next;
    return next;
  }

  function greetAloud() {
    const message = fillGreeting();
    if (!message) return;
    window.SightraTTS?.speak(message, { immediate: true });
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function fillPreferences() {
    const a11y = readA11y();
    const theme = localStorage.getItem("sightra_theme") || localStorage.getItem("theme") || "light";
    const parts = [];
    if (a11y.largeText) parts.push("Larger text");
    if (a11y.highContrast) parts.push("High contrast");
    if (a11y.reduceMotion) parts.push("Reduced motion");
    if (a11y.voiceFeedback) parts.push("Spoken UI feedback");
    setText("dash-pref-theme", theme === "dark" ? "Dark" : "Light");
    const voiceLabels = { sarah: "Sarah", rachel: "Rachel", charlotte: "Charlotte", adam: "Adam", liam: "Liam", brian: "Brian" };
    setText("dash-pref-voice", voiceLabels[a11y.readingVoice] || (a11y.voiceGender === "male" ? "Adam" : "Sarah"));
    setText("dash-pref-language", LANG[a11y.spokenLanguage] || "English");
    setText("dash-pref-a11y", parts.length ? parts.join(", ") : "Default");
  }

  document.addEventListener("DOMContentLoaded", () => {
    fillGreeting();
    fillPreferences();
    greetAloud();
  });
  window.addEventListener("sightra:theme", fillPreferences);
  window.addEventListener("sightra:a11y", fillPreferences);
})();
