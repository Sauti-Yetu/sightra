(function () {
  const DB_NAME = "sightra_voice_clone";
  const STORE = "samples";
  const KEY = "preferred";
  const MAX_MS = 20000;
  const MIN_MS = 4000;

  const recordBtn = document.getElementById("voice-clone-record");
  const stopBtn = document.getElementById("voice-clone-stop");
  const playBtn = document.getElementById("voice-clone-play");
  const deleteBtn = document.getElementById("voice-clone-delete");
  const statusEl = document.getElementById("voice-clone-status");
  const meterEl = document.getElementById("voice-clone-meter");
  const customOption = document.querySelector('#settings-reading-voice option[value="custom"]');

  if (!recordBtn) return;

  let recorder = null;
  let chunks = [];
  let stream = null;
  let startedAt = 0;
  let limitTimer = null;
  let previewUrl = "";
  let previewAudio = null;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function setRecording(on) {
    recordBtn.hidden = on;
    stopBtn.hidden = !on;
    recordBtn.setAttribute("aria-pressed", on ? "true" : "false");
    if (meterEl) meterEl.classList.toggle("is-recording", on);
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) {
          req.result.createObjectStore(STORE);
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function saveSample(blob, durationMs) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(
        { blob, durationMs, mimeType: blob.type || "audio/webm", createdAt: Date.now() },
        KEY
      );
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async function loadSample() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).get(KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  async function clearSample() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).delete(KEY);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  function revokePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = "";
    if (previewAudio) {
      previewAudio.pause();
      previewAudio = null;
    }
  }

  function enableCustom(hasSample) {
    if (!customOption) return;
    customOption.disabled = !hasSample;
    customOption.textContent = hasSample
      ? "My recorded voice (sample saved)"
      : "My recorded voice (record a sample first)";
  }

  async function refresh() {
    revokePreview();
    try {
      const sample = await loadSample();
      const has = !!(sample && sample.blob);
      enableCustom(has);
      playBtn.disabled = !has;
      deleteBtn.disabled = !has;
      if (!has) {
        setStatus("No sample saved yet. Record a short reading of the prompt below.");
        return;
      }
      previewUrl = URL.createObjectURL(sample.blob);
      const seconds = Math.max(1, Math.round((sample.durationMs || 0) / 1000));
      setStatus(
        `Sample saved (${seconds}s). Preview it here. Training a clone for spoken guidance comes in a later release — the sample stays on this device.`
      );
    } catch {
      enableCustom(false);
      playBtn.disabled = true;
      deleteBtn.disabled = true;
      setStatus("Could not open the on-device voice sample store.");
    }
  }

  function mimeType() {
    const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
    if (!window.MediaRecorder) return "";
    return types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  }

  function stopTracks() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setStatus("Voice recording needs a supported browser and microphone access.");
      return;
    }
    const ok = await window.SightraPrivacy?.requireFeatureConsent?.(
      window.SightraPrivacy.CONSENT_MIC,
      "Voice cloning records a short sample on this device. Allow microphone access?"
    );
    if (ok === false) {
      setStatus("Microphone consent is needed to record a voice sample.");
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    } catch {
      setStatus("Could not reach the microphone. Check permission, then try again.");
      return;
    }
    chunks = [];
    const type = mimeType();
    recorder = type ? new MediaRecorder(stream, { mimeType: type }) : new MediaRecorder(stream);
    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size) chunks.push(event.data);
    };
    recorder.onstop = async () => {
      window.clearTimeout(limitTimer);
      setRecording(false);
      stopTracks();
      const durationMs = Date.now() - startedAt;
      if (durationMs < MIN_MS || !chunks.length) {
        setStatus("Recording was too short. Hold for a few seconds and read the prompt.");
        recorder = null;
        return;
      }
      const blob = new Blob(chunks, { type: recorder.mimeType || type || "audio/webm" });
      recorder = null;
      try {
        await saveSample(blob, durationMs);
        await refresh();
        window.SightraUI?.announce("Voice sample saved on this device");
      } catch {
        setStatus("Could not save the sample on this device.");
      }
    };
    startedAt = Date.now();
    recorder.start();
    setRecording(true);
    setStatus("Recording… read the prompt in a clear, steady voice.");
    window.SightraUI?.announce("Recording voice sample");
    limitTimer = window.setTimeout(() => stopRecording(), MAX_MS);
  }

  function stopRecording() {
    if (recorder && recorder.state === "recording") recorder.stop();
    else {
      setRecording(false);
      stopTracks();
    }
  }

  recordBtn.addEventListener("click", startRecording);
  stopBtn.addEventListener("click", stopRecording);
  playBtn.addEventListener("click", () => {
    if (!previewUrl) return;
    if (previewAudio) {
      previewAudio.pause();
      previewAudio = null;
      setStatus("Preview stopped.");
      return;
    }
    previewAudio = new Audio(previewUrl);
    previewAudio.onended = () => {
      previewAudio = null;
    };
    previewAudio.play().catch(() => {
      setStatus("Could not play the saved sample.");
    });
  });
  deleteBtn.addEventListener("click", async () => {
    try {
      await clearSample();
      const select = document.getElementById("settings-reading-voice");
      if (select && select.value === "custom") {
        select.value = "sarah";
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      await refresh();
      window.SightraUI?.announce("Voice sample deleted");
    } catch {
      setStatus("Could not delete the saved sample.");
    }
  });

  refresh();
})();
