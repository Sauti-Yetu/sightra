(function () {
  const MODE_LABELS = {
    live: "Live text",
    document: "Document",
    signage: "Signage",
    currency: "Currency",
    upload: "Upload",
  };

  const video = document.getElementById("readerCamera");
  const canvas = document.getElementById("readerCanvas");
  const spokenEl = document.getElementById("readerSpoken");
  const transcriptEl = document.getElementById("readerTranscript");
  const statusEl = document.getElementById("readerStatus");
  const modeLabel = document.getElementById("readerModeLabel");
  const fileInput = document.getElementById("readerFile");
  const enableBtn = document.getElementById("readerEnableCamera");

  let mode = "live";
  let liveTimer = null;
  let busy = false;
  let lastSpoken = "";
  let lastText = "";
  let stream = null;

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

  function showResult(spoken, text) {
    lastSpoken = spoken || "";
    lastText = text || spoken || "";
    if (spokenEl) spokenEl.textContent = lastSpoken || "Nothing read yet.";
    if (transcriptEl) transcriptEl.textContent = lastText || "No transcript.";
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
      showEnable(false);
      setStatus("Camera ready. Tap the shutter to read.");
      return stream;
    } catch (err) {
      stream = null;
      showEnable(true);
      setStatus((err && err.message) || "Camera permission is needed. You can still upload a photo.");
      return null;
    }
  }

  function captureFrame() {
    if (window.SightraCamera) return window.SightraCamera.capture(video, canvas, 0.7);
    if (!video || !canvas || !video.videoWidth) return "";
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.7);
  }

  async function analyze(frameData) {
    if (!frameData || busy) return;
    busy = true;
    setStatus("Reading…");
    try {
      const headers = { "Content-Type": "application/json" };
      const token = csrf();
      if (token) headers["X-CSRFToken"] = token;
      const res = await fetch("/api/vision/reader/analyze/", {
        method: "POST",
        credentials: "same-origin",
        headers,
        body: JSON.stringify({ frame_data: frameData, mode, language: language() }),
      });
      const data = await res.json();
      if (res.status === 403 && data.code === "consent_required") {
        await ensureConsent();
        setStatus("Grant consent, then try again.");
        return;
      }
      const spoken = data.spoken || data.error || "Nothing found.";
      const text = data.text || spoken;
      showResult(spoken, text);
      window.SightraTTS?.speak(spoken);
      setStatus(MODE_LABELS[mode] + " ready.");
    } catch {
      setStatus("Could not reach the reader service.");
    } finally {
      busy = false;
    }
  }

  async function readNow() {
    const ok = await ensureConsent();
    if (!ok) return;
    if (mode === "upload") {
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
    await analyze(frame);
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
    if (mode !== "live") return;
    const btn = document.getElementById("readerLiveBtn");
    const icon = document.getElementById("readerLiveIcon");
    if (btn) btn.setAttribute("aria-pressed", "true");
    if (icon) icon.textContent = "pause";
    liveTimer = window.setInterval(() => {
      if (!busy) readNow();
    }, 4500);
    readNow();
  }

  function setMode(next) {
    mode = MODE_LABELS[next] ? next : "live";
    document.querySelectorAll("[data-reader-mode]").forEach((btn) => {
      const on = btn.getAttribute("data-reader-mode") === mode;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (modeLabel) modeLabel.textContent = MODE_LABELS[mode];
    stopLive();
    setStatus(
      mode === "upload"
        ? "Upload a photo of a document, sign, or note."
        : "Tap the shutter to read. Live text can run continuously."
    );
    window.SightraUI?.announce(MODE_LABELS[mode] + " mode");
    if (mode === "upload") fileInput?.click();
  }

  document.querySelectorAll("[data-reader-mode]").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.getAttribute("data-reader-mode")));
  });
  document.getElementById("readerCaptureBtn")?.addEventListener("click", readNow);
  document.getElementById("readerRepeatBtn")?.addEventListener("click", () => {
    if (lastSpoken) window.SightraTTS?.speak(lastSpoken);
  });
  document.getElementById("readerLiveBtn")?.addEventListener("click", () => {
    if (mode !== "live") setMode("live");
    if (liveTimer) stopLive();
    else startLive();
  });
  document.getElementById("readerUploadBtn")?.addEventListener("click", () => {
    setMode("upload");
  });
  enableBtn?.addEventListener("click", () => startCamera());
  fileInput?.addEventListener("change", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    const ok = await ensureConsent();
    if (!ok) return;
    const reader = new FileReader();
    reader.onload = () => analyze(String(reader.result || ""));
    reader.readAsDataURL(file);
    fileInput.value = "";
  });

  window.addEventListener("sightra:command", (event) => {
    const { action, mode: cmdMode } = event.detail || {};
    if (action === "reader-mode" && cmdMode) setMode(cmdMode);
    if (action === "scan" || action === "read-now") readNow();
    if (action === "upload") setMode("upload");
    if (action === "repeat" && lastSpoken) window.SightraTTS?.speak(lastSpoken);
    if (action === "stop") {
      stopLive();
      window.SightraTTS?.stop();
    }
  });

  startCamera();
  window.addEventListener("sightra:privacy-onboarded", () => startCamera());
})();
