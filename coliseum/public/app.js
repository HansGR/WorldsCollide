"use strict";

const fighters = {
  a: document.querySelector('.fighter[data-side="a"]'),
  b: document.querySelector('.fighter[data-side="b"]'),
};
let current = null;     // {a, b} enemy records
let busy = false;       // lock during the result animation

async function loadPair() {
  busy = true;
  try {
    const res = await fetch("/api/pair");
    current = await res.json();
    render("a", current.a);
    render("b", current.b);
    fighters.a.classList.remove("chosen", "faded");
    fighters.b.classList.remove("chosen", "faded");
    busy = false;
  } catch (e) {
    console.error(e);
  }
}

function render(side, enemy) {
  const el = fighters[side];
  const img = el.querySelector(".sprite");
  const wrap = el.querySelector(".sprite-wrap");
  wrap.classList.remove("noimg");
  img.classList.remove("missing");

  // Local sprite first, then the CoN CDN as a fallback, then a "?" placeholder.
  const sources = [enemy.sprite, enemy.sprite_cdn].filter(Boolean);
  let idx = 0;
  img.onerror = () => {
    idx += 1;
    if (idx < sources.length) {
      img.src = sources[idx];
    } else {
      img.classList.add("missing");
      wrap.classList.add("noimg");
    }
  };
  img.alt = enemy.name;
  if (sources.length) {
    img.src = sources[0];
  } else {
    img.classList.add("missing");
    wrap.classList.add("noimg");
  }

  el.querySelector(".name").textContent = enemy.name;

  // Location (with a Coliseum tag when relevant) instead of level/HP.
  let loc = enemy.location || "";
  if (enemy.coliseum && !/colosseum/i.test(loc)) {
    loc += (loc ? " &middot; " : "") + '<span class="tag">Coliseum</span>';
  }
  el.querySelector(".location").innerHTML = loc || "&mdash;";

  // Non-scaling stat block.
  for (const i of el.querySelectorAll(".stats i")) {
    const v = enemy[i.dataset.k];
    i.textContent = (v === null || v === undefined) ? "?" : v;
  }

  el.querySelector(".desc").textContent = enemy.description || "";
}

async function vote(winnerSide) {
  if (busy || !current) return;
  busy = true;
  const winner = current[winnerSide];
  const loser = current[winnerSide === "a" ? "b" : "a"];

  fighters[winnerSide].classList.add("chosen");
  fighters[winnerSide === "a" ? "b" : "a"].classList.add("faded");

  try {
    await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ winner: winner.slug, loser: loser.slug }),
    });
  } catch (e) {
    console.error(e);
  }

  refreshStats();
  setTimeout(loadPair, 280);
}

fighters.a.addEventListener("click", () => vote("a"));
fighters.b.addEventListener("click", () => vote("b"));
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") vote("a");
  else if (e.key === "ArrowRight") vote("b");
});
document.getElementById("skip").addEventListener("click", (e) => {
  e.preventDefault();
  if (!busy) loadPair();
});

// --- stats + live tier list ------------------------------------------------
async function refreshStats() {
  try {
    const s = await (await fetch("/api/stats")).json();
    document.getElementById("vote-count").textContent = s.total_votes;
    document.getElementById("coverage").textContent =
      s.unrated > 0 ? `${s.unrated} enemies still unrated` : `avg uncertainty ±${s.avg_rd}`;
  } catch (e) { /* ignore */ }
}

// Tier thresholds applied to Glicko rating (tunable client-side display only).
const TIERS = [
  { label: "S", min: 1750, color: "#ff7676" },
  { label: "A", min: 1600, color: "#ffb24a" },
  { label: "B", min: 1480, color: "#ffe14a" },
  { label: "C", min: 1360, color: "#9be15d" },
  { label: "D", min: 1240, color: "#5dd6e1" },
  { label: "E", min: 0,    color: "#9aa0d6" },
];

async function showStandings() {
  const data = await (await fetch("/api/standings")).json();
  const buckets = TIERS.map((t) => ({ ...t, items: [] }));
  for (const e of data.standings) {
    (buckets.find((t) => e.rating >= t.min) || buckets[buckets.length - 1]).items.push(e);
  }
  const root = document.getElementById("tiers");
  root.innerHTML = "";
  for (const t of buckets) {
    if (!t.items.length) continue;
    const row = document.createElement("div");
    row.className = "tier-row";
    const chips = t.items.map((e) => {
      const img = e.sprite ? `<img src="${e.sprite}" alt="" onerror="this.remove()">` : "";
      return `<span class="chip">${img}${e.name} <span class="r">${e.rating}</span></span>`;
    }).join("");
    row.innerHTML =
      `<div class="tier-label" style="background:${t.color}">${t.label}</div>` +
      `<div class="tier-items">${chips}</div>`;
    root.appendChild(row);
  }
}

document.getElementById("toggle-standings").addEventListener("click", (e) => {
  e.preventDefault();
  const panel = document.getElementById("standings");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) showStandings();
});

loadPair();
refreshStats();
