const video = document.getElementById("camera");
const canvas = document.getElementById("capture");
const message = document.getElementById("message");
const flip = document.getElementById("flip");
const shell = document.getElementById("camera-shell");

let stream = null;
let facingMode = "environment";
let intervalMs = 1200;
let timer = null;
let ready = false;

function post(type, data = {}) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...data }, "*");
}

function reportHeight() {
  post("streamlit:setFrameHeight", { height: Math.ceil(shell.getBoundingClientRect().height) });
}

function stopCamera() {
  if (stream) stream.getTracks().forEach((track) => track.stop());
  stream = null;
}

async function startCamera() {
  stopCamera();
  ready = false;
  message.textContent = "Starting camera…";
  message.hidden = false;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: { ideal: facingMode },
        width: { ideal: 1280 },
        height: { ideal: 960 }
      }
    });
    video.srcObject = stream;
    await video.play();
    ready = true;
    message.hidden = true;
    reportHeight();
  } catch (error) {
    message.textContent = "Camera unavailable. Allow camera access in your browser, then reload this page.";
    message.hidden = false;
    reportHeight();
  }
}

function captureFrame() {
  if (!ready || video.readyState < 2 || !video.videoWidth) return;
  const maxWidth = 960;
  const scale = Math.min(1, maxWidth / video.videoWidth);
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  post("streamlit:setComponentValue", { value: canvas.toDataURL("image/jpeg", 0.82) });
}

function scheduleCapture() {
  if (timer) clearInterval(timer);
  timer = setInterval(captureFrame, intervalMs);
}

flip.addEventListener("click", async () => {
  facingMode = facingMode === "environment" ? "user" : "environment";
  await startCamera();
});

window.addEventListener("message", (event) => {
  if (event.data?.type !== "streamlit:render") return;
  intervalMs = Number(event.data.args?.intervalMs) || 1200;
  if (!timer) scheduleCapture();
});

window.addEventListener("beforeunload", stopCamera);
new ResizeObserver(reportHeight).observe(shell);
post("streamlit:componentReady", { apiVersion: 1 });
reportHeight();
startCamera();
