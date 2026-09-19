// Tiny hand-authored pixel-art bust generator. One shared 14x14 shape
// (hat/hair/face/collar), recolored and lightly remixed per chef so every
// avatar stays crisp and consistent instead of five hand-drawn grids.
const SIZE = 14;

// region codes: 0 empty, 1 hat, 2 hair, 3 skin, 4 eye, 5 mouth, 6 neckerchief, 7 coat, 9 glasses rim
const BASE_SHAPE = [
  [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
  [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
  [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
  [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
  [0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0],
  [0, 0, 2, 3, 4, 3, 3, 3, 3, 4, 3, 2, 0, 0],
  [0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0],
  [0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0],
  [0, 0, 0, 3, 3, 5, 5, 5, 5, 3, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 7, 6, 6, 6, 6, 7, 0, 0, 0, 0],
  [0, 0, 0, 7, 6, 6, 6, 6, 6, 6, 7, 0, 0, 0],
  [0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0],
];

export const CHEF_AVATARS = {
  ramsey: { hairColor: "#e8b84b", skinColor: "#f2c299", accentColor: "#de5030", hat: true, hairStyle: "short", glasses: false, wideSmile: false },
  vikas: { hairColor: "#241a12", skinColor: "#c98a55", accentColor: "#b97322", hat: true, hairStyle: "short", glasses: true, glassesColor: "#2b2b2b", wideSmile: false },
  martin: { hairColor: "#1c140d", skinColor: "#e0b48a", accentColor: "#277862", hat: true, hairStyle: "short", glasses: false, wideSmile: true },
  prue: { hairColor: "#e8e6df", skinColor: "#f2c9a8", accentColor: "#8a4f79", hat: false, hairStyle: "bob", glasses: true, glassesColor: "#e8433a", wideSmile: false },
  alexis: { hairColor: "#2b2118", skinColor: "#f0c9a0", accentColor: "#4c8a57", hat: true, hairStyle: "short", glasses: false, wideSmile: false },
};

function buildGrid(traits) {
  const grid = BASE_SHAPE.map((row) => row.slice());

  if (!traits.hat) {
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < SIZE; c++) if (grid[r][c] === 1) grid[r][c] = 2;
    }
  }

  if (traits.hairStyle === "bob") {
    grid[8][2] = 2; grid[8][11] = 2;
    grid[9][3] = 2; grid[9][10] = 2;
  }

  if (traits.wideSmile) {
    grid[8][3] = 5; grid[8][10] = 5;
  }

  if (traits.glasses) {
    grid[5][3] = 9; grid[5][10] = 9;
  }

  return grid;
}

const REGION_COLOR = {
  1: "#ffffff",
  2: (t) => t.hairColor,
  3: (t) => t.skinColor,
  4: "#2b2b2b",
  5: "#8a3b32",
  6: (t) => t.accentColor,
  7: "#fffdf7",
  9: (t) => t.glassesColor || "#2b2b2b",
};

export function renderPixelAvatarSVG(chefId) {
  const traits = CHEF_AVATARS[chefId] || CHEF_AVATARS.ramsey;
  const grid = buildGrid(traits);
  let rects = "";
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const code = grid[r][c];
      if (!code) continue;
      const fill = typeof REGION_COLOR[code] === "function" ? REGION_COLOR[code](traits) : REGION_COLOR[code];
      rects += `<rect x="${c}" y="${r}" width="1" height="1" fill="${fill}"/>`;
    }
  }
  return `<svg class="pixel-avatar" viewBox="0 0 ${SIZE} ${SIZE}" shape-rendering="crispEdges" aria-hidden="true">${rects}</svg>`;
}
