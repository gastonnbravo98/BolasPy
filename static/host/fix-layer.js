import { Container, Graphics, Text } from "./pixi.js";

const FONT = "Fredoka, ui-rounded, sans-serif";
const LABELS = {
  rocket: "¡COHETE!",
  giant: "¡GIGANTE!",
  shockwave: "¡ONDA DE CHOQUE!",
  swap: "¡INTERCAMBIO!",
};

function makeText(label) {
  const text = new Text({
    text: label,
    style: { fontFamily: FONT, fontSize: 30, fontWeight: "600", fill: 0xffb703, stroke: { color: 0x231f5c, width: 6 } },
  });
  text.anchor.set(0.5, 1);
  return text;
}

function makeRing(radius) {
  return new Graphics().circle(0, 0, radius).stroke({ width: 6, color: 0xffffff });
}

export class FxLayer extends Container {
  #items = [];

  constructor(shockRadius) {
    super();
    this.shockRadius = shockRadius;
  }

  burst(kind, x, y) {
    this.#floatText(LABELS[kind] ?? kind, x, y);
    if (kind === "shockwave") this.#ring(x, y);
  }

  update(dt) {
    const alive = [];
    for (const item of this.#items) {
      item.age += dt;
      const progress = Math.min(1, item.age / item.life);
      item.animate(item.view, progress);
      if (progress < 1) alive.push(item);
      else item.view.destroy();
    }
    this.#items = alive;
  }

  #floatText(label, x, y) {
    const view = makeText(label);
    view.position.set(x, y - 30);
    this.#add(view, 1.4, (v, p) => {
      v.y = y - 30 - 90 * p;
      v.alpha = 1 - p * p;
    });
  }

  #ring(x, y) {
    const view = makeRing(this.shockRadius);
    view.position.set(x, y);
    this.#add(view, 0.6, (v, p) => {
      v.scale.set(0.2 + 0.8 * p);
      v.alpha = 1 - p;
    });
  }

  #add(view, life, animate) {
    this.addChild(view);
    this.#items.push({ view, life, age: 0, animate });
  }
}