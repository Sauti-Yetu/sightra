(function () {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const REC_LANG = {
    en: "en-US",
    sw: "sw-KE",
    fr: "fr-FR",
    ar: "ar-SA",
    so: "so-SO",
    ki: "en-KE",
  };
  let recognition = null;
  let listening = false;

  function a11y() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}");
    } catch {
      return {};
    }
  }

  function enabled() {
    return a11y().voiceCommands === true;
  }

  function status(text) {
    const el = document.getElementById("voice-command-status");
    if (el) el.textContent = text;
    window.SightraUI?.announce(text);
  }

  function go(path) {
    if (window.location.pathname.replace(/\/$/, "") === path.replace(/\/$/, "")) return;
    window.location.href = path;
  }

  function dispatch(action, extra) {
    window.dispatchEvent(new CustomEvent("sightra:command", { detail: { action, ...(extra || {}) } }));
  }

  function onReader() {
    return window.location.pathname.startsWith("/reader");
  }

  function onVision() {
    return window.location.pathname.startsWith("/vision");
  }

  function parse(transcript) {
    const t = (transcript || "").toLowerCase().trim();
    if (!t) return null;
    if (/\b(help|what can i say|commands|msaada)\b/.test(t)) return { action: "help" };
    if (/\b(home|dashboard|go home|nyumbani)\b/.test(t)) return { action: "home" };
    if (/\b(settings|preferences|mipangilio)\b/.test(t)) return { action: "settings" };
    if (/\b(vision|look around|what('s| is) around|ona)\b/.test(t)) return { action: "vision" };
    if (/\b(reader|lookout|read text|read this|soma)\b/.test(t)) return { action: "reader" };
    if (/\b(upload|pakia)\b/.test(t)) return { action: "upload" };
    if (/\b(document|letter|page|waraka)\b/.test(t)) return { action: "reader-mode", mode: "document" };
    if (/\b(currency|money|banknote|note|pesa)\b/.test(t)) return { action: "reader-mode", mode: "currency" };
    if (/\b(sign|signage|label|menu|alama)\b/.test(t)) return { action: "reader-mode", mode: "signage" };
    if (/\b(live text)\b/.test(t)) return { action: "reader-mode", mode: "live" };
    if (/\b(scan|start scan|read now|anza)\b/.test(t)) return { action: "scan" };
    if (/\b(stop|pause|cancel|quiet|simama)\b/.test(t)) return { action: "stop" };
    if (/\b(repeat|again|rudia)\b/.test(t)) return { action: "repeat" };
    return { action: "unknown", transcript: t };
  }

  function run(cmd) {
    if (!cmd) return;
    if (cmd.action === "help") {
      const msg =
        "Say home, vision, reader, settings, scan, document, currency, signage, upload, repeat, or stop.";
      status(msg);
      window.SightraTTS?.speak(msg);
      return;
    }
    if (cmd.action === "home") return go("/dashboard");
    if (cmd.action === "vision") return go("/vision/");
    if (cmd.action === "reader") return go("/reader/");
    if (cmd.action === "settings") return go("/settings/");
    if (cmd.action === "stop") {
      window.SightraTTS?.stop();
      dispatch("stop");
      status("Stopped.");
      return;
    }
    if (cmd.action === "scan") {
      if (!onVision() && !onReader()) return go("/vision/");
      dispatch("scan");
      return;
    }
    if (cmd.action === "upload" || cmd.action === "reader-mode") {
      if (!onReader()) return go("/reader/");
      dispatch(cmd.action, cmd);
      return;
    }
    dispatch(cmd.action, cmd);
    if (cmd.action === "unknown") status("I heard: " + cmd.transcript);
  }

  function start() {
    if (!SpeechRec) {
      status("Voice commands need a browser with speech recognition, such as Chrome.");
      return;
    }
    if (listening) return;
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = REC_LANG[a11y().spokenLanguage || "en"] || "en-US";
    recognition.onresult = (event) => {
      const last = event.results[event.results.length - 1];
      if (!last || !last.isFinal) return;
      const text = last[0].transcript;
      status("Heard: " + text);
      run(parse(text));
    };
    recognition.onerror = () => {
      listening = false;
      syncUi();
    };
    recognition.onend = () => {
      if (listening && enabled()) {
        try {
          recognition.start();
        } catch {
          listening = false;
          syncUi();
        }
      }
    };
    try {
      recognition.start();
      listening = true;
      status("Listening for commands.");
      syncUi();
    } catch {
      status("Could not start the microphone.");
    }
  }

  function stopListen() {
    listening = false;
    try {
      recognition?.stop();
    } catch {
      /* ignore */
    }
    status("Voice commands paused.");
    syncUi();
  }

  function syncUi() {
    const bar = document.getElementById("voice-command-bar");
    const btn = document.getElementById("voice-command-toggle");
    if (!bar || !btn) return;
    if (!enabled()) {
      bar.hidden = true;
      return;
    }
    bar.hidden = false;
    btn.setAttribute("aria-pressed", listening ? "true" : "false");
    btn.classList.toggle("is-listening", listening);
  }

  function onA11yChange() {
    syncUi();
    if (enabled() && !listening) start();
    if (!enabled() && listening) stopListen();
  }

  function init() {
    const bar = document.getElementById("voice-command-bar");
    const btn = document.getElementById("voice-command-toggle");
    if (!bar || !btn) return;
    btn.addEventListener("click", () => {
      if (!enabled()) {
        status("Turn on voice commands in Settings first.");
        return;
      }
      if (listening) stopListen();
      else start();
    });
    syncUi();
    if (enabled()) start();
    window.addEventListener("sightra:a11y", onA11yChange);
  }

  document.addEventListener("DOMContentLoaded", init);
  window.SightraVoice = { start, stop: stopListen, parse, run, enabled };
})();
