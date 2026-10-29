(function () {
  let currentAudio = null;

  const DEVICE_LANG = {
    en: "en-US",
    sw: "sw-KE",
    fr: "fr-FR",
    ar: "ar-SA",
    so: "so-SO",
    ki: "en-KE",
  };

  function prefs() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}");
    } catch {
      return {};
    }
  }

  function gender() {
    return prefs().voiceGender === "male" ? "male" : "female";
  }

  function language() {
    return prefs().spokenLanguage || "en";
  }

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function deviceSpeak(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = DEVICE_LANG[language()] || "en-US";
    const voices = window.speechSynthesis.getVoices();
    const wantMale = gender() === "male";
    const langPrefix = (utter.lang || "en").slice(0, 2);
    const match =
      voices.find((v) => {
        const name = (v.name || "").toLowerCase();
        const sameLang = (v.lang || "").toLowerCase().startsWith(langPrefix);
        const genderHit = wantMale ? /male|daniel|alex|fred|george/.test(name) : /female|samantha|karen|moira|zira|samantha|sarah/.test(name);
        return sameLang && genderHit;
      }) || voices.find((v) => (v.lang || "").toLowerCase().startsWith(langPrefix));
    if (match) utter.voice = match;
    window.speechSynthesis.speak(utter);
  }

  async function speak(text, opts = {}) {
    const cleaned = (text || "").trim();
    if (!cleaned) return;
    stop();
    try {
      const headers = { "Content-Type": "application/json" };
      const token = csrf();
      if (token) headers["X-CSRFToken"] = token;
      const res = await fetch("/api/audio/speak/", {
        method: "POST",
        credentials: "same-origin",
        headers,
        body: JSON.stringify({
          text: cleaned,
          gender: opts.gender || gender(),
          language: opts.language || language(),
        }),
      });
      if (!res.ok) {
        deviceSpeak(cleaned);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      currentAudio = new Audio(url);
      currentAudio.onended = () => {
        URL.revokeObjectURL(url);
        currentAudio = null;
      };
      await currentAudio.play();
    } catch {
      deviceSpeak(cleaned);
    }
  }

  function stop() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    window.speechSynthesis?.cancel();
  }

  window.SightraTTS = { speak, stop, deviceSpeak, gender, language };
})();
