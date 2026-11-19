import { connect } from "/static/shared/socket.js";
import { Hud } from "./hud.js";
import { Scene } from "./scene.js";

const BOARD_ROWS = 6;
const hud = new Hud();
const state = { scene: null, players: new Map(), finished: [] };

// ---- mensajes del servidor -----------------------------------------
async function onInit(msg) {
  hud.setJoinUrl(msg.join_url);
  hud.setPhase(msg.phase);
  hud.setCount(msg.players.length);
  msg.players.forEach((p) => state.players.set(p.id, p));
  state.scene ??= await Scene.create(document.getElementById("stage"), msg);
  state.players.forEach((p) => state.scene.marbles.addPlayer(p));
}

function onPlayerJoined(msg) {
  state.players.set(msg.player.id, msg.player);
  state.scene?.marbles.addPlayer(msg.player);
  hud.setCount(msg.count);
}

function onPhase(msg) {
  hud.setPhase(msg.phase);
  hud.setCount(msg.players);
  if (msg.phase === "racing") startRace();
  if (msg.phase === "lobby") state.scene?.marbles.hideAll();
}

function startRace() {
  state.finished = [];
  state.scene?.marbles.hideAll();
  state.scene?.boxes.showAll();
  hud.showBoard([]);
}

function onSnapshot(msg) {
  state.scene?.marbles.applySnapshot(msg.marbles);
  state.scene?.movers.apply(msg.movers);
  hud.showBoard(buildBoard(msg.marbles));
}

function onFinish(msg) {
  state.finished.push(msg);
}

function onResults(msg) {
  hud.showPodium(msg.podium);
}

function onBoxTaken(msg) {
  state.scene?.boxes.take(msg.box, msg.respawn_s);
}

function onPowerupUsed(msg) {
  state.scene?.fx.burst(msg.kind, msg.x, msg.y);
}

// ---- tabla de posiciones -------------------------------------------
function finishedRows() {
  return state.finished.map((f) => ({ text: `${f.rank}. ${f.name}`, color: f.color }));
}

function runnerRows(marbles, offset, limit) {
  return [...marbles]
    .sort((a, b) => b[2] - a[2])
    .slice(0, limit)
    .map(([id], index) => ({ id, rank: offset + index + 1 }))
    .filter(({ id }) => state.players.has(id))
    .map(({ id, rank }) => ({ text: `${rank}. ${state.players.get(id).name}`, color: state.players.get(id).color }));
}

function buildBoard(marbles) {
  const done = finishedRows();
  const room = Math.max(0, BOARD_ROWS - done.length);
  return [...done.slice(0, BOARD_ROWS), ...runnerRows(marbles, done.length, room)];
}

// ---- arranque ------------------------------------------------------
const handlers = {
  init: onInit,
  player_joined: onPlayerJoined,
  phase: onPhase,
  snapshot: onSnapshot,
  finish: onFinish,
  results: onResults,
  box_taken: onBoxTaken,
  powerup_used: onPowerupUsed,
};

const socket = connect("/ws/host", (msg) => handlers[msg.type]?.(msg));

window.addEventListener("keydown", (event) => {
  if (event.code === "Space") socket.send({ type: "start" });
});