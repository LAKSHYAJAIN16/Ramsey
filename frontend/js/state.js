const RECENT_KEY = "ramsey_recent_recipes";
const SESSION_KEY = "ramsey_session_id";
const PROGRESS_KEY = "ramsey_healthy_progress";

const DEFAULT_PROGRESS = { calories: 0, meals: 0, xp: 0, streak: 0, lastMealDate: null, loggedDishes: [], chefPack: "ramsey" };

export const DAILY_MENUS = [
  { dish: "Mediterranean chickpea bowl", calories: 480, tag: "fibre-forward", detail: "Chickpeas, greens, lemon & grains", emoji: "🥙" },
  { dish: "Ginger vegetable stir-fry", calories: 420, tag: "20 min", detail: "Crisp veg, tofu & brown rice", emoji: "🥬" },
  { dish: "Herby shakshuka", calories: 390, tag: "protein-rich", detail: "Eggs, tomatoes & fresh herbs", emoji: "🍳" },
];

export const MASTERCHEF_CHALLENGES = [
  { dish: "beef wellington", time: "3 hr challenge", skill: "Sear · duxelles · pastry", emoji: "🥩" },
  { dish: "lobster ravioli", time: "2 hr challenge", skill: "Fresh pasta · shellfish sauce", emoji: "🦞" },
  { dish: "chocolate soufflé", time: "90 min challenge", skill: "Meringue · precision bake", emoji: "🍫" },
  { dish: "risotto alla milanese", time: "75 min challenge", skill: "Stock control · emulsification", emoji: "🍚" },
];

export const CHEF_PACKS = [
  { id: "ramsey", name: "Ramsey", focus: "Everyday healthy", mark: "R", accent: "tomato" },
  { id: "vikas", name: "Vikas Khanna", focus: "Indian wellness", mark: "VK", accent: "saffron" },
  { id: "martin", name: "Martin Yan", focus: "Fast Asian cooking", mark: "MY", accent: "jade" },
  { id: "prue", name: "Prue Leith", focus: "Better baking", mark: "PL", accent: "plum" },
  { id: "alexis", name: "Alexis Gauthier", focus: "Plant-forward", mark: "AG", accent: "leaf" },
];

export function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = `cook-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return { dish: params.get("q"), demo: params.get("demo") === "1" };
}

export function getRecentDishes() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
  } catch {
    return [];
  }
}

export function pushRecentDish(dish) {
  const recents = getRecentDishes().filter((d) => d.toLowerCase() !== dish.toLowerCase());
  recents.unshift(dish);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recents.slice(0, 6)));
}

export function getProgress() {
  try { return { ...DEFAULT_PROGRESS, ...JSON.parse(localStorage.getItem(PROGRESS_KEY)) }; }
  catch { return { ...DEFAULT_PROGRESS }; }
}

function saveProgress(progress) {
  localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
  return progress;
}

export function selectChefPack(packId) {
  return saveProgress({ ...getProgress(), chefPack: packId });
}

export function logHealthyMeal(dish, calories) {
  const progress = getProgress();
  const today = new Date().toISOString().slice(0, 10);
  if (progress.loggedDishes.some((entry) => entry.date === today && entry.dish === dish)) return { progress, duplicate: true };
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  const streak = progress.lastMealDate === today ? progress.streak : progress.lastMealDate === yesterday ? progress.streak + 1 : 1;
  const next = {
    ...progress,
    calories: progress.lastMealDate === today ? progress.calories + calories : calories,
    meals: progress.lastMealDate === today ? progress.meals + 1 : 1,
    xp: progress.xp + 20,
    streak,
    lastMealDate: today,
    loggedDishes: [...progress.loggedDishes, { dish, date: today, calories }].slice(-60),
  };
  return { progress: saveProgress(next), duplicate: false };
}
