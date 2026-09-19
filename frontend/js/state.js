let RECENT_KEY, SESSION_KEY, PROGRESS_KEY;
export function setProfileScope(uid) {
  RECENT_KEY = `ramsey_recent_recipes_${uid}`;
  SESSION_KEY = `ramsey_session_id_${uid}`;
  PROGRESS_KEY = `ramsey_healthy_progress_${uid}`;
}

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

export const TUTORIALS = [
  { id: "chop", icon: "🔪", title: "Chop with control", time: "8 min", goal: "Turn uneven prep into even cooking.", safety: "Keep fingertips curled under in a claw grip; guide the blade with your knuckles, never your fingertips.", steps: ["Square off the ingredient so it has a flat, stable side.", "Plant the knife tip, then use a relaxed rocking motion.", "Work slowly for uniform pieces—speed comes after control."], drill: "Dice half an onion into even 1 cm pieces." },
  { id: "saute", icon: "🍳", title: "Sauté without steaming", time: "7 min", goal: "Build colour and flavour instead of soggy vegetables.", safety: "Use a dry pan and keep handles turned away from the edge of the stove.", steps: ["Preheat the pan before adding oil.", "Add ingredients in one loose layer; do not crowd the pan.", "Leave food alone long enough to brown, then toss or turn."], drill: "Sauté sliced mushrooms until deeply golden." },
  { id: "boil", icon: "💨", title: "Boil and blanch", time: "6 min", goal: "Cook through while keeping colour and texture.", safety: "Lower food into water away from you and keep a lid nearby, not on a rolling boil.", steps: ["Salt the water until it tastes pleasantly seasoned.", "Wait for a steady rolling boil before adding food.", "Taste before draining; shock vegetables in ice water when you want them crisp."], drill: "Blanch green beans, then cool them in ice water." },
  { id: "season", icon: "🧂", title: "Season as you go", time: "5 min", goal: "Make layers of flavour, not a last-minute salt rush.", safety: "Add small pinches, taste, and adjust—especially with salty stock, cheese, or soy sauce.", steps: ["Season ingredients at each stage, not only at the finish.", "Balance salt with acid, sweetness, heat, or fat.", "Taste with a clean spoon after every meaningful change."], drill: "Season a simple tomato sauce in three small adjustments." },
  { id: "pan", icon: "🔥", title: "Read your pan", time: "6 min", goal: "Know when heat is helping and when it is burning your food.", safety: "Never leave hot oil unattended; if it smokes, remove the pan from heat and let it cool.", steps: ["Start medium and give the pan time to heat evenly.", "Listen for a gentle sizzle, not a violent crackle.", "Adjust heat before food burns—the pan retains heat after the dial moves."], drill: "Toast spices gently until fragrant, then remove them before they darken." },
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
  return { dish: params.get("q"), demo: params.get("demo") === "1", mode: params.get("mode") };
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
