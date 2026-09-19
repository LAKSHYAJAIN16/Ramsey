import * as api from "./api.js?v=quest-first-1";
import * as ui from "./ui.js?v=quest-first-1";
import { signInWithGoogle } from "./firebase-auth.js";
import { CHEF_PACKS, DAILY_MENUS, MASTERCHEF_CHALLENGES, TUTORIALS, getProgress, getQueryParams, getRecentDishes, getSessionId, logHealthyMeal, pushRecentDish, selectChefPack, setProfileScope } from "./state.js?v=quest-first-1";
import { setupSessionControls } from "./session-controls.js?v=quest-first-1";

let sessionId;
const localMemory = { allergies: [], dislikes: [] };
let mealToLog = null;
let selectedTutorial = TUTORIALS[0];
let currentPath = DAILY_MENUS;

// Duolingo-style lesson path: dishes already cooked today are done, the
// first uncooked one is playable, everything after it is locked until
// that lesson is cleared.
function annotatePath(menus) {
  const today = new Date().toISOString().slice(0, 10);
  const doneToday = new Set(
    getProgress().loggedDishes.filter((entry) => entry.date === today).map((entry) => entry.dish.toLowerCase())
  );
  let unlockedNext = true;
  return menus.map((menu) => {
    const complete = doneToday.has(menu.dish.toLowerCase());
    let status;
    if (complete) status = "complete";
    else if (unlockedNext) { status = "current"; unlockedNext = false; }
    else status = "locked";
    return { ...menu, status };
  });
}

function renderPath(onPick) {
  ui.renderDailyMenu(annotatePath(currentPath), onPick);
}

async function loadRecipe(dish, demo = false, dailyMenu = null) {
  ui.setSearchStatus(true, demo ? ["Loading offline demo recipe..."] : [
    "Racing: fast fetch + parse",
    "Racing: live browser fallback",
    "First valid recipe wins, the rest get cancelled",
  ]);
  try {
    const recipe = await api.getRecipe(sessionId, dish || "demo", demo);
    if (dish) pushRecentDish(dish);
    ui.setSearchStatus(false);
    ui.showScreen("kitchen");
    const state = await api.getSessionState(sessionId);
    ui.renderKitchenState(state);
    mealToLog = dailyMenu || { dish: recipe.title, calories: 450 };
    const source = document.getElementById('recipe-source'); source.replaceChildren();
    if (recipe.method === 'demo') source.textContent = 'Bundled demo recipe — not a live recipe search.';
    else if (/^https?:\/\//.test(recipe.source_url)) {
      const link = document.createElement('a'); link.href = recipe.source_url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = 'View original recipe source'; source.appendChild(link);
    }
  } catch (err) {
    ui.showScreen('launcher');
    ui.setSearchStatus(true, [err.message || 'Recipe search failed. Try another dish.']);
  }
}

function setupLauncher() {
  ui.renderRecentDishes(getRecentDishes(), (dish) => loadRecipe(dish));
  ui.renderProgress(getProgress());
  api.getMe().then(ui.renderAccount).catch(() => ui.renderAccount({ authenticated: false, oauth_ready: false }));
  document.getElementById("auth-button").addEventListener("click", async () => {
    const button = document.getElementById("auth-button");
    const original = button.textContent;
    button.disabled = true;
    button.textContent = "Signing in...";
    try {
      const account = await signInWithGoogle();
      ui.renderAccount(account);
    } catch (err) {
      console.error("Google sign-in failed:", err);
      button.disabled = false;
      button.textContent = original;
    }
  });
  renderPath((menu) => loadRecipe(menu.dish, false, menu));
  document.getElementById("campaign-fridge-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    const status = document.getElementById("campaign-plan-status");
    status.classList.remove("hidden");
    status.textContent = "Reading your fridge and building a lesson path...";
    try {
      const result = await api.analyzeFridgePhoto(file);
      const plan = result.suggestions.map((dish, index) => ({
        dish, calories: 350 + index * 60, emoji: ["🥕", "🍳", "🍲"][index] || "🍽️",
        tag: `Lesson ${index + 1}`, detail: `${index === 0 ? "Start here" : "Unlock after the lesson before"} · from your fridge`,
      }));
      if (!plan.length) throw new Error("No dishes found");
      currentPath = plan;
      renderPath((menu) => loadRecipe(menu.dish, false, menu));
      status.textContent = `Your path is ready: ${result.ingredients.slice(0, 5).join(", ")}. Start Lesson 1.`;
    } catch (err) {
      status.textContent = "I couldn't build a plan from that image. Try a brighter, closer fridge photo.";
    }
  });
  ui.renderMasterChefChallenges(MASTERCHEF_CHALLENGES, (challenge) => loadRecipe(challenge.dish));
  const showTutorial = (tutorial) => {
    selectedTutorial = tutorial;
    ui.renderTutorials(TUTORIALS, selectedTutorial.id, showTutorial);
    ui.renderTutorialDetail(selectedTutorial);
  };
  showTutorial(selectedTutorial);
  const renderPacks = () => ui.renderChefPacks(CHEF_PACKS, getProgress().chefPack, (pack) => {
    selectChefPack(pack.id);
    renderPacks();
  });
  renderPacks();
  document.getElementById("mode-campaign").addEventListener("click", () => ui.setCookingMode("campaign"));
  document.getElementById("mode-freestyle").addEventListener("click", () => ui.setCookingMode("freestyle"));
  document.getElementById("mode-masterchef").addEventListener("click", () => ui.setCookingMode("masterchef"));

  document.getElementById("dish-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const dish = document.getElementById("dish-input").value.trim();
    if (dish) loadRecipe(dish);
  });

  document.getElementById("demo-button").addEventListener("click", () => loadRecipe(null, true));

  document.getElementById("fridge-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = ""; // allow picking the same file again later
    if (!file) return;

    const status = document.getElementById("fridge-status");
    const suggestions = document.getElementById("fridge-suggestions");
    suggestions.innerHTML = "";
    status.classList.remove("hidden");
    status.textContent = "Looking at your fridge...";

    try {
      const result = await api.analyzeFridgePhoto(file);
      status.classList.add("hidden");
      if (!result.suggestions.length) {
        status.classList.remove("hidden");
        status.textContent = "Couldn't make out enough to suggest anything - try a closer photo.";
        return;
      }
      result.suggestions.forEach((dish) => {
        const btn = document.createElement("button");
        btn.textContent = dish;
        btn.addEventListener("click", () => loadRecipe(dish));
        suggestions.appendChild(btn);
      });
    } catch (err) {
      status.textContent = `Couldn't read that photo: ${err.message}`;
    }
  });
}

function setupKitchenControls() {
  document.getElementById('btn-exit').addEventListener('click', () => {
    ui.showScreen('launcher'); api.getMe().then(ui.renderAccount).catch(() => {});
    ui.renderProgress(getProgress()); renderPath(menu => loadRecipe(menu.dish, false, menu));
  });
  let polling = false;
  setInterval(async () => {
    if (polling || document.getElementById('kitchen').classList.contains('hidden')) return;
    polling = true;
    try { ui.renderKitchenState(await api.getSessionState(sessionId)); }
    catch (error) { document.getElementById('session-connection').textContent = error.message; }
    finally { polling = false; }
  }, 2000);
}

function startApp(account) {
  setProfileScope(account.uid); sessionId = getSessionId();
  document.getElementById('sign-in-gate').classList.add('hidden');
  document.getElementById('overlay').classList.remove('hidden');
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/app/sw.js").catch(() => {});
  setupLauncher();
  setupKitchenControls();
  setupSessionControls(sessionId);

  const { dish, demo, mode } = getQueryParams();
  if (["campaign", "freestyle", "masterchef"].includes(mode)) ui.setCookingMode(mode);
  if (dish || demo) loadRecipe(dish, demo);
}

async function main() {
  const status = document.getElementById('sign-in-status');
  const button = document.getElementById('sign-in-start');
  button.disabled = true;
  try {
    const account = await api.getMe();
    if (account.authenticated) { startApp(account); return; }
    status.textContent = account.oauth_ready ? 'Your recipes and points belong to your account.' : 'Google sign-in is not configured on the desktop server.';
    button.disabled = !account.oauth_ready;
  } catch { status.textContent = 'Cannot reach the desktop server. Start it, then reload this page.'; }
  button.addEventListener('click', async () => {
    button.disabled = true; status.textContent = 'Opening Google sign-in…';
    try { startApp(await signInWithGoogle()); }
    catch (error) { status.textContent = error.message; button.disabled = false; }
  });
}
main();
