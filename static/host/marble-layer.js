import { Container, Graphics, Text } from "./pixi.js";

const FONT = "Fredoka, ui-rounded, sans-serif";
const LABEL_STYLE = { fontFamily: FONT, fontSize: 15, fill: 0xffffff, stroke: { color: 0x231f5c, width: 4 } };
const BADGE_STYLE = { fontFamily: FONT, fontSize: 20, fill: 0xffb703, stroke: { color: 0x231f5c, width: 4 } };

function makeLabel(name, radius) {
  const label = new Text({ text: name, style: LABEL_STYLE });
  label.anchor.set(0.5, 1);
  label.y = -radius - 2;
  return label;
}

function makeBadge(radius) {
  const badge = new Text({ text: "★", style: BADGE_STYLE });
  badge.anchor.set(0.5);
  badge.position.set(radius + 4, -radius);
  badge.visible = false;
  return badge;
}

function makeView(player, radius) {
  const view = new Container();
  const ball = new Graphics().circle(0, 0, radius).fill(player.color).stroke({ width: 2, color: 0xffffff });
  const shine = new Graphics()
    .circle(-radius * 0.35, -radius * 0.35, radius * 0.25)
    .fill({ color: 0xffffff, alpha: 0.6 });
  view.badge = makeBadge(radius); // ★ = tiene un power-up guardado
  view.addChild(ball, shine, makeLabel(player.name, radius), view.badge);
  view.visible = false;
  return view;
}

export class MarbleLayer extends Container {
  #entries = new Map();

  constructor(radius) {
    super();
    this.radius = radius;
  }

  addPlayer(player) {
    if (this.#entries.has(player.id)) return;
    const view = makeView(player, this.radius);
    this.addChild(view);
    this.#entries.set(player.id, { view, tx: 0, ty: 0, ts: 1, placed: false });
  }

  applySnapshot(marbles) {
    marbles.forEach((marble) => this.#moveTo(...marble));
    const seen = new Set(marbles.map(([id]) => id));
    this.#hideWhere(([id]) => !seen.has(id));
  }

  hideAll() {
    this.#hideWhere(() => true);
    this.#entries.forEach((entry) => (entry.placed = false));
  }

  update() {
    this.#visible().forEach((entry) => this.#ease(entry));
  }

  leaderY() {
    return this.#visible().reduce((max, entry) => Math.max(max, entry.ty), 0);
  }

  // ---- privados ----
  #visible() {
    return [...this.#entries.values()].filter((entry) => entry.view.visible);
  }

  #hideWhere(predicate) {
    [...this.#entries].filter(predicate).forEach(([, entry]) => (entry.view.visible = false));
  }

  #moveTo(id, x, y, radius, held) {
    const entry = this.#entries.get(id);
    if (!entry) return;
    entry.tx = x;
    entry.ty = y;
    entry.ts = radius / this.radius;
    entry.view.badge.visible = Boolean(held);
    if (!entry.placed) this.#snap(entry);
    entry.placed = true;
    entry.view.visible = true;
  }

  #snap(entry) {
    entry.view.position.set(entry.tx, entry.ty);
    entry.view.scale.set(entry.ts);
  }

  #ease(entry) {
    const { view } = entry;
    view.x += (entry.tx - view.x) * 0.35;
    view.y += (entry.ty - view.y) * 0.35;
    view.scale.set(view.scale.x + (entry.ts - view.scale.x) * 0.2);
  }
}