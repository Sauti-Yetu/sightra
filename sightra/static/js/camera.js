(function () {
  function isMobile() {
    return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "");
  }

  function prepare(video) {
    if (!video) return;
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "true");
    video.playsInline = true;
    video.muted = true;
    video.autoplay = true;
  }

  function stopStream(stream) {
    if (stream && stream.getTracks) {
      stream.getTracks().forEach((track) => track.stop());
    }
  }

  function videoTrack(stream) {
    return stream && stream.getVideoTracks ? stream.getVideoTracks()[0] : null;
  }

  function waitForFrame(video, timeoutMs) {
    const timeout = timeoutMs || 5000;
    if (video && video.videoWidth > 0) return Promise.resolve(true);
    return new Promise((resolve) => {
      if (!video) {
        resolve(false);
        return;
      }
      let done = false;
      const finish = (ok) => {
        if (done) return;
        done = true;
        window.clearTimeout(timer);
        video.removeEventListener("loadedmetadata", onReady);
        video.removeEventListener("loadeddata", onReady);
        video.removeEventListener("playing", onReady);
        resolve(ok);
      };
      const onReady = () => {
        if (video.videoWidth > 0) finish(true);
      };
      const timer = window.setTimeout(() => finish(video.videoWidth > 0), timeout);
      video.addEventListener("loadedmetadata", onReady);
      video.addEventListener("loadeddata", onReady);
      video.addEventListener("playing", onReady);
    });
  }

  async function videoInputs() {
    if (!navigator.mediaDevices?.enumerateDevices) return [];
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter((d) => d.kind === "videoinput");
  }

  function rankDevices(devices) {
    const preferBack = isMobile();
    const score = (device) => {
      const label = (device.label || "").toLowerCase();
      const back = /back|rear|environment|wide|ultra/i.test(label);
      const front = /front|user|face|facetime|webcam/i.test(label);
      if (preferBack) return back ? 0 : front ? 2 : 1;
      return front ? 0 : back ? 2 : 1;
    };
    return [...devices].sort((a, b) => score(a) - score(b));
  }

  function constraintList(devices) {
    const list = [];
    rankDevices(devices).forEach((device) => {
      if (device.deviceId) {
        list.push({ video: { deviceId: { ideal: device.deviceId } }, audio: false });
      }
    });
    if (isMobile()) {
      list.push({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 24 },
        },
        audio: false,
      });
      list.push({ video: { facingMode: { ideal: "environment" } }, audio: false });
    } else {
      list.push({
        video: { facingMode: { ideal: "user" }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
    }
    list.push({ video: true, audio: false });
    return list;
  }

  function friendlyError(err) {
    const name = err && err.name;
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      return "Camera permission is blocked. Allow the camera for Sightra in browser settings, then tap Enable camera.";
    }
    if (name === "NotReadableError" || name === "AbortError") {
      return "The camera is busy in another app. Close it, then tap Enable camera.";
    }
    if (name === "OverconstrainedError") {
      return "Could not match this camera. Tap Enable camera to try again.";
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      return "No camera was found. On a computer, allow camera access in system settings, then tap Enable camera.";
    }
    return (err && err.message) || "Could not start the camera.";
  }

  function capabilities(stream) {
    const track = videoTrack(stream);
    try {
      return (track && track.getCapabilities && track.getCapabilities()) || {};
    } catch {
      return {};
    }
  }

  function hasTorch(stream) {
    return !!capabilities(stream).torch;
  }

  async function setNightMode(stream, enabled) {
    const track = videoTrack(stream);
    const result = { torch: false, torchSupported: false, exposure: false };
    if (!track) return result;
    const caps = capabilities(stream);
    result.torchSupported = !!caps.torch;
    const advanced = [];
    if (caps.torch) advanced.push({ torch: !!enabled });
    if (caps.exposureCompensation) {
      const max =
        typeof caps.exposureCompensation.max === "number" ? caps.exposureCompensation.max : 2;
      advanced.push({ exposureCompensation: enabled ? max : 0 });
    }
    const modes = [].concat(caps.exposureMode || []);
    if (enabled && modes.includes("continuous")) {
      advanced.push({ exposureMode: "continuous" });
    }
    try {
      if (advanced.length) await track.applyConstraints({ advanced });
      result.torch = !!(caps.torch && enabled);
      result.exposure = !!(caps.exposureCompensation && enabled);
    } catch {
      if (caps.torch) {
        try {
          await track.applyConstraints({ advanced: [{ torch: !!enabled }] });
          result.torch = !!enabled;
        } catch {
          result.torch = false;
        }
      }
    }
    try {
      await track.applyConstraints({
        frameRate: enabled ? { ideal: 15, max: 24 } : { ideal: 30 },
      });
    } catch {
      /* some browsers reject frameRate after start */
    }
    return result;
  }

  const lumaCanvas = document.createElement("canvas");

  function measureLuma(video) {
    if (!video || !video.videoWidth) return -1;
    const w = 48;
    const h = Math.max(1, Math.round((video.videoHeight / video.videoWidth) * w));
    lumaCanvas.width = w;
    lumaCanvas.height = h;
    const ctx = lumaCanvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return -1;
    ctx.drawImage(video, 0, 0, w, h);
    const pixels = ctx.getImageData(0, 0, w, h).data;
    let sum = 0;
    const n = pixels.length / 4;
    for (let i = 0; i < pixels.length; i += 4) {
      sum += 0.2126 * pixels[i] + 0.7152 * pixels[i + 1] + 0.0722 * pixels[i + 2];
    }
    return sum / n;
  }

  function enhanceLowLight(ctx, width, height) {
    const img = ctx.getImageData(0, 0, width, height);
    const d = img.data;
    let sum = 0;
    const n = d.length / 4;
    for (let i = 0; i < d.length; i += 4) {
      sum += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
    }
    const mean = sum / n;
    if (mean >= 72) return { mean, enhanced: false };
    const target = 118;
    const gain = Math.min(mean < 28 ? 3.1 : 2.3, target / Math.max(10, mean));
    const lift = Math.min(55, Math.max(8, target - mean) * 0.45);
    const gamma = mean < 32 ? 0.58 : 0.72;
    for (let i = 0; i < d.length; i += 4) {
      for (let c = 0; c < 3; c += 1) {
        let v = d[i + c] * gain + lift;
        v = 255 * Math.pow(Math.min(255, Math.max(0, v)) / 255, gamma);
        d[i + c] = v;
      }
    }
    ctx.putImageData(img, 0, 0);
    return { mean, enhanced: true };
  }

  async function start(video) {
    if (!video) throw new Error("Camera view is missing.");
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw new Error("Camera needs HTTPS (or localhost) and a supported browser.");
    }
    prepare(video);
    if (video.srcObject && video.videoWidth) {
      await video.play().catch(() => {});
      return video.srcObject;
    }

    let devices = [];
    try {
      devices = await videoInputs();
    } catch {
      devices = [];
    }

    let lastErr = null;
    const tried = constraintList(devices);
    for (const constraints of tried) {
      let stream = null;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (video.srcObject && video.srcObject !== stream) stopStream(video.srcObject);
        video.srcObject = stream;
        await video.play().catch(() => {});
        const ready = await waitForFrame(video, 2500);
        if (!ready) {
          stopStream(stream);
          if (video.srcObject === stream) video.srcObject = null;
          throw new Error("Camera started but no picture yet.");
        }
        return stream;
      } catch (err) {
        lastErr = err;
        if (stream) stopStream(stream);
        if (video.srcObject === stream) video.srcObject = null;
      }
    }
    throw new Error(friendlyError(lastErr));
  }

  function capture(video, canvas, quality, maxDim, options) {
    if (!video || !canvas || !video.videoWidth) return "";
    let width = video.videoWidth;
    let height = video.videoHeight;
    const cap = Number(maxDim) || 0;
    if (cap > 0 && Math.max(width, height) > cap) {
      const scale = cap / Math.max(width, height);
      width = Math.max(1, Math.round(width * scale));
      height = Math.max(1, Math.round(height * scale));
    }
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(video, 0, 0, width, height);
    const force = options && options.lowLight;
    const luma = measureLuma(video);
    if (force === true || (force !== false && luma >= 0 && luma < 72)) {
      enhanceLowLight(ctx, width, height);
    }
    return canvas.toDataURL("image/jpeg", quality || 0.7);
  }

  function stop(video) {
    const stream = video && video.srcObject;
    stopStream(stream);
    if (video) video.srcObject = null;
  }

  window.SightraCamera = {
    start,
    waitForFrame,
    capture,
    stop,
    prepare,
    setNightMode,
    hasTorch,
    measureLuma,
  };
})();
