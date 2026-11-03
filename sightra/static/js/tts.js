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

  const READING_VOICES = {
    sarah: { gender: "female", hints: /sarah|female|samantha|karen|moira|zira/i },
    rachel: { gender: "female", hints: /rachel|female|samantha|karen/i },
    charlotte: { gender: "female", hints: /charlotte|female|moira|zira/i },
    adam: { gender: "male", hints: /adam|male|daniel|alex|fred|george/i },
    liam: { gender: "male", hints: /liam|male|daniel|alex/i },
    brian: { gender: "male", hints: /brian|male|fred|george/i },
  };

  function prefs() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}");
    } catch {
      return {};
    }
  }

  function clamp(value, min, max, fallback) {
    const n = Number(value);
    if (!Number.isFinite(n)) return fallback;
    return Math.min(max, Math.max(min, n));
  }

  function readingVoice() {
    const key = (prefs().readingVoice || "").toLowerCase();
    if (READING_VOICES[key]) return key;
    return gender() === "male" ? "adam" : "sarah";
  }

  function gender() {
    const voice = READING_VOICES[(prefs().readingVoice || "").toLowerCase()];
    if (voice) return voice.gender;
    return prefs().voiceGender === "male" ? "male" : "female";
  }

  function language() {
    return prefs().spokenLanguage || "en";
  }

  function rate() {
    return clamp(prefs().speechRate, 0.7, 1.4, 1);
  }

  function pitch() {
    return clamp(prefs().speechPitch, 0.7, 1.4, 1);
  }

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function pickDeviceVoice(utter) {
    const voices = window.speechSynthesis.getVoices();
    const voiceKey = readingVoice();
    const meta = READING_VOICES[voiceKey] || READING_VOICES.sarah;
    const langPrefix = (utter.lang || "en").slice(0, 2);
    return (
      voices.find((v) => {
        const sameLang = (v.lang || "").toLowerCase().startsWith(langPrefix);
        return sameLang && meta.hints.test(v.name || "");
      }) || voices.find((v) => (v.lang || "").toLowerCase().startsWith(langPrefix))
    );
  }

  function deviceSpeak(text) {
    return new Promise((resolve) => {
      if (!window.speechSynthesis || !text) {
        resolve();
        return;
      }
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = DEVICE_LANG[language()] || "en-US";
      utter.rate = rate();
      utter.pitch = pitch();
      const match = pickDeviceVoice(utter);
      if (match) utter.voice = match;
      utter.onend = () => resolve();
      utter.onerror = () => resolve();
      window.speechSynthesis.speak(utter);
    });
  }

  async function speak(text, opts = {}) {
    const cleaned = (text || "").trim();
    if (!cleaned) return;
    stop();
    if (opts.immediate) {
      await deviceSpeak(cleaned);
      return;
    }
    try {
      const headers = { "Content-Type": "application/json" };
      const token = csrf();
      if (token) headers["X-CSRFToken"] = token;
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), 4000);
      let res;
      try {
        res = await fetch("/api/audio/speak/", {
          method: "POST",
          credentials: "same-origin",
          headers,
          signal: controller.signal,
          body: JSON.stringify({
            text: cleaned,
            gender: opts.gender || gender(),
            language: opts.language || language(),
            voice: opts.voice || readingVoice(),
          }),
        });
      } finally {
        window.clearTimeout(timer);
      }
      if (!res.ok) {
        await deviceSpeak(cleaned);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      currentAudio = new Audio(url);
      currentAudio.playbackRate = rate();
      currentAudio.onended = () => {
        URL.revokeObjectURL(url);
        currentAudio = null;
      };
      await currentAudio.play();
    } catch {
      await deviceSpeak(cleaned);
    }
  }

  function stop() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    window.speechSynthesis?.cancel();
  }

  window.SightraTTS = { speak, stop, deviceSpeak, gender, language, rate, pitch, readingVoice };
})();
