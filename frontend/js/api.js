const API_BASE = "";

async function checkedJson(response) {
  if (!response.ok) {
    let detail;
    try { detail = (await response.json()).detail; } catch {}
    throw new Error(typeof detail === 'string' ? detail : `Couldn't reach Ramsey (${response.status}). Check the desktop server and try again.`);
  }
  return response.json();
}

export async function createPairCode(sessionId) {
  return checkedJson(await fetch(`/api/session/${encodeURIComponent(sessionId)}/pair`, { method: 'POST' }));
}

export async function checkFood(sessionId, photo) {
  const form = new FormData(); form.append('session_id', sessionId); form.append('photo', photo); form.append('plating', 'true');
  return checkedJson(await fetch('/api/vision/assist', { method: 'POST', body: form }));
}

export async function getRecipe(sessionId, dish, demo = false) {
  const params = new URLSearchParams({ session_id: sessionId, dish, demo: demo ? "1" : "0" });
  const res = await fetch(`${API_BASE}/api/recipe?${params}`);
  return checkedJson(res);
}

export async function getSessionState(sessionId) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
  return checkedJson(res);
}

export async function sendAction(sessionId, action, index = null) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, index }),
  });
  return checkedJson(res);
}

export async function sendChat(sessionId, text) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  return checkedJson(res);
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
  return checkedJson(res);
}
