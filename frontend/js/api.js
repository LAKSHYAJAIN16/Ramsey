const API_BASE = "";

export async function getRecipe(sessionId, dish, demo = false) {
  const params = new URLSearchParams({ session_id: sessionId, dish, demo: demo ? "1" : "0" });
  const res = await fetch(`${API_BASE}/api/recipe?${params}`);
  if (!res.ok) throw new Error(`recipe fetch failed: ${res.status}`);
  return res.json();
}

export async function getSessionState(sessionId) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
  return res.json();
}

export async function sendAction(sessionId, action, index = null) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, index }),
  });
  return res.json();
}

export async function sendChat(sessionId, text) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  return res.json();
}

export async function sendSafetyCommand(phrase) {
  const res = await fetch(`${API_BASE}/api/safety/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phrase }),
  });
  if (!res.ok) throw new Error(`safety command failed: ${res.status}`);
  return res.json();
}

export async function getMe() {
  const res = await fetch(`${API_BASE}/api/me`);
  if (!res.ok) throw new Error(`profile fetch failed: ${res.status}`);
  return res.json();
}

export async function saveCompletedMeal(calories) {
  const res = await fetch(`${API_BASE}/api/me/progress`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ calories }),
  });
  if (!res.ok) throw new Error(`profile progress save failed: ${res.status}`);
  return res.json();
}

export async function analyzeFridgePhoto(photoFile) {
  const form = new FormData();
  form.append("photo", photoFile);
  const res = await fetch(`${API_BASE}/api/fridge/analyze`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`fridge analysis failed: ${res.status}`);
  return res.json();
}

export async function sendVoice(sessionId, audioBlob) {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("audio", audioBlob, "utterance.webm");
  const res = await fetch(`${API_BASE}/api/chat/voice`, { method: "POST", body: form });
  return res.json();
}
