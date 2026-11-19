import { connect } from "/static/shared/socket.js";

const $ = (id) => document.getElementById(id);
const KEY_ID = "marbles.id";
const KEY_NAME = "marbles.name";
const KEY_COLOR = "marbles.color";

const PALETTE = ["#ff5d73", "#ffb703", "#2ec4b6", "#4cc9f0", "#b388ff", "#ff8fab", "#9ef01a", "#ffffff"];

const POWERUPS = {
  rocket: { name: "Cohete", hint: "Te dispara hacia adelante." },
  giant: { name: "Gigante", hint: "Más grande y pesada por 6 segundos." },
  shockwave: { name: "Onda de choque", hint: "Empuja a las bolitas que tenés cerca." },
  swap: { name: "Intercambio", hint: "Cambiás de lugar con una que va adelante." },
};
const DEFAULT_HINT = "Tocá para empujar tu bolita. Pasá por las cajas ? para conseguir un power-up.";

// ---- identidad (sin crypto.randomUUID: no existe en http) -----------
function newId() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function loadId() {
  const saved = localStorage.getItem(KEY_ID);
  if (saved) return saved;
  const id = newId();
  localStorage.setItem(KEY_ID, id);
  return id;
}

function randomColor() {
  return PALETTE[Math.floor(Math.random() * PALETTE.length)];
}

const state = {
  id: loadId(),
  color: localStorage.getItem(KEY_COLOR) ?? randomColor(),
  joined: false,
  inRace: false,
  rank: null,
  held: null,
};

// ---- selector de color ----------------------------------------------
function paintMine(color) {
  document.documentElement.style.setProperty("--mine", color);
}

function pickColor(color) {
  state.color = color;
  $("color").value = color;
  paintMine(color);
  localStorage.setItem(KEY_COLOR, color);
  document.querySelectorAll(".swatch").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.color === color));
  });
}

function makeSwatch(color) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "swatch";
  button.dataset.color = color;
  button.style.background = color;
  button.setAttribute("aria-label", `Color ${color}`);
  button.addEventListener("click", () => pickColor(color));
  return button;
}

function setupColorPicker() {
  $("swatches").replaceChildren(...PALETTE.map(makeSwatch));
  $("color").addEventListener("input", (event) => pickColor(event.target.value));
  pickColor(state.color);
}

// ---- pantallas ------------------------------------------------------
function showScreen(name) {
  document.querySelectorAll("[data-screen-id]").forEach((el) => {
    el.hidden = el.dataset.screenId !== name;
  });
}

function showLobby(title, text) {
  $("ball").style.background = state.color;
  $("lobby-title").textContent = title;
  $("lobby-text").textContent = text;
  showScreen("lobby");
}

function showRank(rank) {
  $("rank").textContent = rank === 1 ? "¡Ganaste! 🏆" : `Llegaste en el puesto ${rank}`;
  showScreen("done");
}

function applyPhase(phase) {
  if (!state.joined) return showScreen("join");
  if (phase === "racing" && state.inRace) return showScreen("racing");
  if (phase === "racing") return showLobby("Carrera en curso", "Entrás en la próxima ronda.");
  if (phase === "finished" && state.rank) return showRank(state.rank);
  if (phase === "finished") return showLobby("Terminó la carrera", "Mirá la pantalla grande.");
  showLobby("¡Listo, estás adentro!", "Esperá a que empiece la carrera.");
}

// ---- power-up guardado ----------------------------------------------
function renderPowerup() {
  const info = POWERUPS[state.held];
  $("powerup").hidden = !info;
  $("powerup").textContent = info ? `Usar: ${info.name}` : "";
  $("powerup-hint").textContent = info ? info.hint : DEFAULT_HINT;
}

function setHeld(kind) {
  state.held = kind;
  renderPowerup();
}

// ---- mensajes del servidor -----------------------------------------
function onJoined(msg) {
  state.joined = true;
  state.inRace = msg.in_race;
  state.color = msg.color;
  pickColor(msg.color);
  localStorage.setItem(KEY_NAME, msg.name);
  applyPhase(msg.phase);
}

function onPhase(msg) {
  const resets = msg.phase === "lobby" || msg.phase === "racing";
  if (resets) state.rank = null;
  if (resets) setHeld(null);
  if (msg.phase === "racing") state.inRace = state.joined;
  if (msg.phase === "lobby") state.inRace = false;
  applyPhase(msg.phase);
}

function onFinish(msg) {
  state.rank = msg.rank;
  showRank(msg.rank);
}

function onBoost(msg) {
  if (msg.ok) startCooldown(msg.cooldown);
}

function onPowerup(msg) {
  setHeld(msg.kind);
  if (msg.kind && navigator.vibrate) navigator.vibrate(60);
}

function onError() {
  showError("La sala está llena.");
}

function startCooldown(seconds) {
  const button = $("boost");
  button.disabled = true;
  button.style.setProperty("--cd", `${seconds}s`);
  button.classList.add("cooling");
  setTimeout(() => {
    button.disabled = false;
    button.classList.remove("cooling");
  }, seconds * 1000);
}

function showError(text) {
  $("error").textContent = text;
}

// ---- acciones del usuario -------------------------------------------
function sendJoin(name) {
  return socket.send({ type: "join", id: state.id, name, color: state.color });
}

function onSubmit(event) {
  event.preventDefault();
  const name = $("name").value.trim();
  if (!name) return showError("Escribí un nombre para entrar.");
  if (!sendJoin(name)) showError("Sin conexión. Probá de nuevo.");
}

function onSocketOpen() {
  const saved = localStorage.getItem(KEY_NAME);
  if (saved) sendJoin(saved);
}

// ---- arranque -------------------------------------------------------
const handlers = {
  joined: onJoined,
  phase: onPhase,
  finish: onFinish,
  boost: onBoost,
  powerup: onPowerup,
  error: onError,
};
const socket = connect("/ws/player", (msg) => handlers[msg.type]?.(msg), onSocketOpen);

setupColorPicker();
$("name").value = localStorage.getItem(KEY_NAME) ?? "";
$("join-form").addEventListener("submit", onSubmit);
$("boost").addEventListener("click", () => socket.send({ type: "boost" }));
$("powerup").addEventListener("click", () => socket.send({ type: "use" }));