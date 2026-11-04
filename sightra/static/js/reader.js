(function () {
  const MODE_LABELS = {
    live: "Live text",
    document: "Document",
    signage: "Signage",
    currency: "Currency",
    upload: "Document",
  };

  const video = document.getElementById("readerCamera");
  const still = document.getElementById("readerStill");
  const canvas = document.getElementById("readerCanvas");
  const spokenEl = document.getElementById("readerSpoken");
  const transcriptEl = document.getElementById("readerTranscript");
  const statusEl = document.getElementById("readerStatus");
  const modeLabel = document.getElementById("readerModeLabel");
  const fileInput = document.getElementById("readerFile");
  const enableBtn = document.getElementById("readerEnableCamera");
  const sourceCameraBtn = document.getElementById("readerSourceCamera");
  const sourceUploadBtn = document.getElementById("readerSourceUpload");
  const captureBtn = document.getElementById("readerCaptureBtn");
  const nightBtn = document.getElementById("readerNightBtn");

  let mode = "live";
  let source = "camera";
  let liveTimer = null;
  let busy = false;
  let lastSpoken = "";
  let lastText = "";
  let stream = null;
  let readToken = 0;
  let speaking = false;
  let nightForced = localStorage.getItem("sightra_night_lock") === "1";
  let nightActive = false;
  let dimStreak = 0;
  let nightTimer = null;

  function language() {
    try {
      return JSON.parse(localStorage.getItem("sightra_a11y") || "{}").spokenLanguage || "en";
    } catch {
      return "en";
    }
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function setCaptureLabel() {
    if (!captureBtn) return;
    captureBtn.setAttribute("aria-label", source === "upload" ? "Upload a photo to read" : "Read now");
  }

  function showStill(url, { contain = false } = {}) {
    if (!still || !url) return;
    still.src = url;
    still.classList.toggle("object-contain", contain);
    still.classList.toggle("object-cover", !contain);
    still.classList.remove("hidden");
    if (video) video.classList.add("hidden");
  }

  function hideStill() {
    if (still) {
      still.removeAttribute("src");
      still.classList.add("hidden");
    }
    if (video) video.classList.remove("hidden");
  }

  function splitSentences(text) {
    const raw = (text || "").replace(/\s+/g, " ").trim();
    if (!raw) return [];
    const parts = raw.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [raw];
    return parts.map((p) => p.trim()).filter(Boolean);
  }

  function speakChunk(text) {
    speaking = true;
    const cleaned = (text || "").trim();
    if (!cleaned) {
      speaking = false;
      return Promise.resolve();
    }
    if (window.SightraTTS?.deviceSpeak) {
      return window.SightraTTS.deviceSpeak(cleaned).finally(() => {
        speaking = false;
      });
    }
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        speaking = false;
        resolve();
        return;
      }
      const utter = new SpeechSynthesisUtterance(cleaned);
      const langMap = { en: "en-US", sw: "sw-KE", fr: "fr-FR", ar: "ar-SA", so: "so-SO", ki: "en-KE" };
      utter.lang = langMap[language()] || "en-US";
      utter.rate = window.SightraTTS?.rate?.() || 1;
      utter.pitch = window.SightraTTS?.pitch?.() || 1;
      utter.onend = () => {
        speaking = false;
        resolve();
      };
      utter.onerror = () => {
        speaking = false;
        resolve();
      };
      window.speechSynthesis.speak(utter);
    });
  }

  function stopSpeech() {
    speaking = false;
    window.SightraTTS?.stop();
    window.speechSynthesis?.cancel();
  }

  async function streamAndNarrate(spoken, text, token) {
    lastSpoken = spoken || text || "";
    lastText = text || spoken || "";
    if (spokenEl) spokenEl.textContent = lastSpoken || "Nothing read yet.";
    if (transcriptEl) transcriptEl.textContent = "";
    const chunks = splitSentences(lastText);
    if (!chunks.length) {
      if (transcriptEl) transcriptEl.textContent = "No transcript.";
      return;
    }
    for (let i = 0; i < chunks.length; i += 1) {
      if (token !== readToken) return;
      const soFar = chunks.slice(0, i + 1).join(" ");
      if (transcriptEl) {
        transcriptEl.textContent = soFar;
        transcriptEl.scrollTop = transcriptEl.scrollHeight;
      }
      await speakChunk(chunks[i]);
    }
  }

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  async function ensureConsent() {
    if (!window.SightraPrivacy?.requireFeatureConsent) return true;
    return window.SightraPrivacy.requireFeatureConsent(
      window.SightraPrivacy.CONSENT_CAMERA,
      "Sightra Reader needs camera analysis consent. Allow now?"
    );
  }

  function showEnable(show) {
    if (!enableBtn) return;
    enableBtn.classList.toggle("hidden", !show);
    enableBtn.textContent = show ? "Enable camera" : "Camera on";
  }

  function setSource(next, { openPicker = false } = {}) {
    source = next === "upload" ? "upload" : "camera";
    sourceCameraBtn?.classList.toggle("is-active", source === "camera");
    sourceUploadBtn?.classList.toggle("is-active", source === "upload");
    sourceCameraBtn?.setAttribute("aria-pressed", source === "camera" ? "true" : "false");
    sourceUploadBtn?.setAttribute("aria-pressed", source === "upload" ? "true" : "false");
    setCaptureLabel();
    stopLive();
    if (source === "camera") {
      hideStill();
      setStatus("Camera ready. Point at the page, then tap the shutter.");
      startCamera();
    } else {
      setStatus("Upload a photo of a document, sign, or note.");
      if (openPicker) fileInput?.click();
    }
    window.SightraUI?.announce(source === "upload" ? "Upload mode" : "Camera mode");
  }

  function setNightButton(on) {
    if (!nightBtn) return;
    nightBtn.classList.toggle("is-on", on);
    nightBtn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  async function applyNight(forceApply) {
    if (!stream || !window.SightraCamera?.setNightMode) return;
    const want = nightForced || dimStreak >= 2;
    if (!forceApply && want === nightActive) {
      setNightButton(nightForced || nightActive);
      return;
    }
    const result = await window.SightraCamera.setNightMode(stream, want);
    nightActive = want;
    setNightButton(nightForced || nightActive);
    if (want) {
      setStatus(result.torch ? "Low light. Torch on." : "Low light. Brightening the picture.");
    }
  }

  function sampleNight() {
    if (!window.SightraCamera?.measureLuma || !video?.videoWidth) return;
    const mean = window.SightraCamera.measureLuma(video);
    if (mean < 45) dimStreak += 1;
    else if (mean > 95) dimStreak = 0;
    else dimStreak = Math.max(0, dimStreak - 1);
    applyNight();
  }

  function startNightWatch() {
    stopNightWatch();
    sampleNight();
    nightTimer = window.setInterval(sampleNight, 700);
  }

  function stopNightWatch() {
    if (nightTimer) {
      window.clearInterval(nightTimer);
      nightTimer = null;
    }
  }

  async function startCamera() {
    if (stream && video && video.videoWidth) return stream;
    if (!window.SightraCamera) {
      setStatus("Camera helper did not load. Refresh and try again.");
      showEnable(true);
      return null;
    }
    try {
      stream = await window.SightraCamera.start(video);
      nightActive = false;
      showEnable(false);
      startNightWatch();
      await applyNight(true);
      if (source === "camera") setStatus("Camera ready. Tap the shutter to read.");
      return stream;
    } catch (err) {
      stream = null;
      showEnable(true);
      setStatus((err && err.message) || "Camera permission is needed. You can still upload a photo.");
      return null;
    }
  }

  function captureFrame() {
    if (window.SightraCamera) {
      return window.SightraCamera.capture(video, canvas, 0.72, 1280, {
        lowLight: nightForced || nightActive,
      });
    }
    if (!video || !canvas || !video.videoWidth) return "";
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.72);
  }

  async function postAnalyze(frameData) {
    const headers = { "Content-Type": "application/json" };
    const token = csrf();
    if (token) headers["X-CSRFToken"] = token;
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 22000);
    const analyzeMode = source === "upload" && mode === "live" ? "upload" : mode;
    try {
      const res = await fetch("/api/vision/reader/analyze/", {
        method: "POST",
        credentials: "same-origin",
        headers,
        signal: controller.signal,
        body: JSON.stringify({ frame_data: frameData, mode: analyzeMode, language: language() }),
      });
      let data = {};
      try {
        data = await res.json();
      } catch {
        data = {};
      }
      return { res, data };
    } finally {
      window.clearTimeout(timer);
    }
  }

  async function analyze(frameData, { freeze = false, contain = false } = {}) {
    if (!frameData) return;
    const token = ++readToken;
    busy = true;
    stopSpeech();
    if (freeze) showStill(frameData, { contain });
    setStatus("Reading…");
    if (spokenEl) spokenEl.textContent = "Reading the page…";
    if (transcriptEl) transcriptEl.textContent = "Text will appear here as it is read aloud.";
    window.SightraUI?.announce("Reading the page");
    try {
      let { res, data } = await postAnalyze(frameData);
      if (token !== readToken) return;
      if (res.status === 403 && data.code === "consent_required") {
        const ok = await ensureConsent();
        if (!ok) {
          setStatus("Grant camera analysis consent, then try again.");
          return;
        }
        ({ res, data } = await postAnalyze(frameData));
      }
      if (token !== readToken) return;
      if (!res.ok && data.code !== "consent_required") {
        const spoken = data.spoken || data.error || "Reading failed. Try again.";
        if (spokenEl) spokenEl.textContent = spoken;
        if (transcriptEl) transcriptEl.textContent = data.text || spoken;
        await speakChunk(spoken);
        setStatus(spoken);
        return;
      }
      const spoken = data.spoken || data.error || "Nothing found.";
      const text = data.text || spoken;
      await streamAndNarrate(spoken, text, token);
      if (token === readToken) setStatus("Reading complete. Tap repeat to hear it again.");
    } catch (err) {
      if (token !== readToken) return;
      const msg =
        err && err.name === "AbortError"
          ? "Reading timed out. Try again."
          : "Could not reach the reader service.";
      setStatus(msg);
      await speakChunk(msg);
    } finally {
      if (token === readToken) busy = false;
    }
  }

  async function readNow() {
    const ok = await ensureConsent();
    if (!ok) return;
    if (source === "upload") {
      fileInput?.click();
      return;
    }
    const cam = await startCamera();
    if (!cam) return;
    await window.SightraCamera?.waitForFrame(video);
    const frame = captureFrame();
    if (!frame) {
      setStatus("Camera is not ready yet. Tap Enable camera, then try again.");
      showEnable(true);
      return;
    }
    await analyze(frame, { freeze: mode !== "live" || !liveTimer, contain: false });
  }

  function stopLive() {
    if (liveTimer) {
      window.clearInterval(liveTimer);
      liveTimer = null;
    }
    const btn = document.getElementById("readerLiveBtn");
    const icon = document.getElementById("readerLiveIcon");
    if (btn) btn.setAttribute("aria-pressed", "false");
    if (icon) icon.textContent = "play_arrow";
  }

  function startLive() {
    stopLive();
    setSource("camera");
    if (mode !== "live") setMode("live", { skipLiveReset: true });
    const btn = document.getElementById("readerLiveBtn");
    const icon = document.getElementById("readerLiveIcon");
    if (btn) btn.setAttribute("aria-pressed", "true");
    if (icon) icon.textContent = "pause";
    liveTimer = window.setInterval(() => {
      if (!busy) readNow();
    }, 4500);
    readNow();
  }

  function setMode(next, { skipLiveReset = false } = {}) {
    const mapped = next === "upload" ? "document" : next;
    mode = MODE_LABELS[mapped] ? mapped : "live";
    document.querySelectorAll("[data-reader-mode]").forEach((btn) => {
      const on = btn.getAttribute("data-reader-mode") === mode;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (modeLabel) modeLabel.textContent = MODE_LABELS[mode];
    if (!skipLiveReset) stopLive();
    window.SightraUI?.announce(MODE_LABELS[mode] + " mode");
  }

  document.querySelectorAll("[data-reader-mode]").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.getAttribute("data-reader-mode")));
  });
  captureBtn?.addEventListener("click", readNow);
  document.getElementById("readerRepeatBtn")?.addEventListener("click", () => {
    if (!lastText && !lastSpoken) return;
    readToken += 1;
    streamAndNarrate(lastSpoken, lastText, readToken);
  });
  document.getElementById("readerLiveBtn")?.addEventListener("click", () => {
    if (liveTimer) stopLive();
    else startLive();
  });
  sourceCameraBtn?.addEventListener("click", () => setSource("camera"));
  sourceUploadBtn?.addEventListener("click", () => setSource("upload", { openPicker: true }));
  enableBtn?.addEventListener("click", () => {
    setSource("camera");
    startCamera();
  });
  nightBtn?.addEventListener("click", async () => {
    nightForced = !nightForced;
    localStorage.setItem("sightra_night_lock", nightForced ? "1" : "0");
    if (nightForced) dimStreak = 3;
    else {
      dimStreak = 0;
      nightActive = false;
    }
    await applyNight(true);
    window.SightraUI?.announce(nightForced ? "Night light on" : "Night light automatic");
  });
  setNightButton(nightForced);
  fileInput?.addEventListener("change", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    if (file.type === "application/pdf" || /\.pdf$/i.test(file.name || "")) {
      setStatus("Upload a photo of the page. PDF files are not read directly.");
      window.SightraUI?.announce("Please upload a photo of the document.");
      fileInput.value = "";
      return;
    }
    if (file.type && !file.type.startsWith("image/")) {
      setStatus("Choose a photo of the document, sign, or note.");
      fileInput.value = "";
      return;
    }
    const ok = await ensureConsent();
    if (!ok) {
      fileInput.value = "";
      return;
    }
    setSource("upload");
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || "");
      showStill(dataUrl, { contain: true });
      analyze(dataUrl, { freeze: true, contain: true });
    };
    reader.onerror = () => setStatus("Could not open that file. Try another photo.");
    reader.readAsDataURL(file);
    fileInput.value = "";
  });

  window.addEventListener("sightra:command", (event) => {
    const { action, mode: cmdMode } = event.detail || {};
    if (action === "reader-mode" && cmdMode) {
      if (cmdMode === "upload") setSource("upload", { openPicker: true });
      else setMode(cmdMode);
    }
    if (action === "scan" || action === "read-now") readNow();
    if (action === "upload") setSource("upload", { openPicker: true });
    if (action === "repeat" && (lastText || lastSpoken)) {
      readToken += 1;
      streamAndNarrate(lastSpoken, lastText, readToken);
    }
    if (action === "stop") {
      readToken += 1;
      stopLive();
      stopSpeech();
    }
  });

  setCaptureLabel();
  startCamera();
  window.addEventListener("sightra:privacy-onboarded", () => startCamera());
})();
