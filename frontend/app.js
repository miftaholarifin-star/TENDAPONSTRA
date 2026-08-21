const API_BASE = "http://127.0.0.1:8000";

const form = document.querySelector("#telemetry-form");
const apiStatus = document.querySelector("#api-status");
const riskStatus = document.querySelector("#risk-status");
const distanceValue = document.querySelector("#distance-value");
const tiltValue = document.querySelector("#tilt-value");
const batteryValue = document.querySelector("#battery-value");
const decisionBox = document.querySelector("#decision-box");
const decisionLabel = document.querySelector("#decision-label");
const decisionReason = document.querySelector("#decision-reason");

async function checkApi() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error("API tidak tersedia");
    apiStatus.textContent = "API terhubung";
    apiStatus.className = "api-status online";
  } catch (error) {
    apiStatus.textContent = "API belum terhubung";
    apiStatus.className = "api-status offline";
  }
}

function renderDecision(payload, result) {
  riskStatus.textContent = result.risk_status;
  distanceValue.textContent = payload.distance_front_cm;
  tiltValue.textContent = payload.tilt_degree;
  batteryValue.textContent = payload.battery_percent;

  const statusClass = result.risk_status.toLowerCase();
  decisionBox.className = `decision ${statusClass}`;
  decisionLabel.textContent = result.risk_status;
  decisionReason.textContent = result.reasons.join(" | ");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    device_id: "TDP-001",
    timestamp: new Date().toISOString(),
    distance_front_cm: Number(document.querySelector("#distance").value),
    tilt_degree: Number(document.querySelector("#tilt").value),
    battery_percent: Number(document.querySelector("#battery").value),
    emergency_button: document.querySelector("#emergency").checked,
  };

  try {
    const response = await fetch(`${API_BASE}/api/v1/telemetry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || "Telemetri ditolak");
    }
    renderDecision(payload, result);
  } catch (error) {
    decisionBox.className = "decision danger";
    decisionLabel.textContent = "GAGAL MEMPROSES";
    decisionReason.textContent = error.message;
  }
});

checkApi();

