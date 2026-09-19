const RECENT_KEY = "ramsey_recent_recipes";
const SESSION_KEY = "ramsey_session_id";

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
