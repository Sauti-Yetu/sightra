(function () {
  const CONSTRAINTS = [
    {
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    },
    { video: { facingMode: "environment" }, audio: false },
    { video: true, audio: false },
  ];

  function prepare(video) {
    if (!video) return;
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "true");
    video.playsInline = true;
    video.muted = true;
    video.autoplay = true;
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

  async function start(video) {
    if (!video) throw new Error("Camera view is missing.");
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw new Error("Camera needs HTTPS (or localhost) and a supported browser.");
    }
    prepare(video);
    if (video.srcObject) {
      await video.play().catch(() => {});
      const ready = await waitForFrame(video);
      if (ready) return video.srcObject;
    }
    let lastErr = null;
    for (const constraints of CONSTRAINTS) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        await video.play().catch(() => {});
        const ready = await waitForFrame(video);
        if (!ready) throw new Error("Camera started but no picture yet.");
        return stream;
      } catch (err) {
        lastErr = err;
      }
    }
    const name = lastErr && lastErr.name;
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      throw new Error("Camera permission is blocked. Allow the camera for Sightra in browser settings.");
    }
    if (name === "NotFoundError" || name === "DevicesNotFoundError") {
      throw new Error("No camera was found on this device.");
    }
    throw new Error((lastErr && lastErr.message) || "Could not start the camera.");
  }

  function capture(video, canvas, quality) {
    if (!video || !canvas || !video.videoWidth) return "";
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", quality || 0.7);
  }

  function stop(video) {
    const stream = video && video.srcObject;
    if (stream && stream.getTracks) {
      stream.getTracks().forEach((track) => track.stop());
    }
    if (video) video.srcObject = null;
  }

  window.SightraCamera = { start, waitForFrame, capture, stop, prepare };
})();
