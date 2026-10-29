(function () {
  const LANG = {
    en: "English",
    sw: "Swahili",
    fr: "French",
    ar: "Arabic",
    so: "Somali",
    ki: "Kikuyu",
  };

  function greetingWord() {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return "Good morning";
    if (hour >= 12 && hour < 17) return "Good afternoon";
    return "Good evening";
  }

  function readA11y() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}");
    } catch {
      return {};
    }
  }

  function fillGreeting() {
    const el = document.getElementById("greeting");
    if (!el) return;
    const name = (el.getAttribute("data-display-name") || "").trim();
    const next = name ? `${greetingWord()}, ${name}.` : `${greetingWord()}.`;
    if (el.textContent !== next) el.textContent = next;
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
    setText("dash-pref-voice", a11y.voiceGender === "male" ? "Male" : "Female");
    setText("dash-pref-language", LANG[a11y.spokenLanguage] || "English");
    setText("dash-pref-a11y", parts.length ? parts.join(", ") : "Default");
  }

  document.addEventListener("DOMContentLoaded", () => {
    fillGreeting();
    fillPreferences();
  });
  window.addEventListener("sightra:theme", fillPreferences);
  window.addEventListener("sightra:a11y", fillPreferences);
})();
