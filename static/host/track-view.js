import { Graphics, Text } from "./pixi.js";

const COLORS = { track: 0xf2e9ff, pin: 0xffb703, finish: 0x2ec4b6 };

function drawSegments(graphics, segments) {
  segments.forEach(([x1, y1, x2, y2]) => graphics.moveTo(x1, y1).lineTo(x2, y2));
  graphics.stroke({ width: 8, color: COLORS.track, cap: "round" });
}

function drawPins(graphics, pegs) {
  pegs.forEach(([x, y, r]) => graphics.circle(x, y, r));
  graphics.fill(COLORS.pin);
}

function drawFinishLine(graphics, config) {
  graphics.rect(0, config.finish_y, config.world_w, 10).fill(COLORS.finish);
}

function finishLabel(config) {
  const label = new Text({
    text: "META",
    style: { fontFamily: "Fredoka, ui-rounded, sans-serif", fontSize: 56, fill: COLORS.finish },
  });
  label.anchor.set(0.5, 0);
  label.position.set(config.world_w / 2, config.finish_y + 24);
  return label;
}

export function drawTrack(track, config) {
  const graphics = new Graphics();
  drawSegments(graphics, track.segments);
  drawPins(graphics, track.pegs);
  drawFinishLine(graphics, config);
  graphics.addChild(finishLabel(config));
  return graphics;
}
