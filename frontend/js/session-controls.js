import * as api from './api.js';

export function setupSessionControls(sessionId) {
  const pair = document.getElementById('btn-pair-quest');
  const pairStatus = document.getElementById('pair-status');
  let pairExpiry;
  pair.addEventListener('click', async () => {
    pair.disabled = true;
    pairStatus.textContent = 'Creating a pairing code…';
    try {
      const result = await api.createPairCode(sessionId);
      pairStatus.textContent = `Quest code: ${result.code}. After the native Quest app is installed, enter this code in its pairing screen to load your selected recipe. Expires in 10 minutes. Headset setup is required first.`;
      clearTimeout(pairExpiry);
      pairExpiry = setTimeout(() => { pairStatus.textContent = 'Code expired. Click Pair Quest for a new code.'; }, result.expires_in * 1000);
    } catch (error) { pairStatus.textContent = error.message; }
    finally { pair.disabled = false; }
  });
}
