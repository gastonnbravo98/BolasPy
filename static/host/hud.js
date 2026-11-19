const $ = (id) => document.getElementById(id);

function listItem(text, color) {
  const item = document.createElement("li");
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.style.background = color;
  const label = document.createElement("span");
  label.textContent = text; // textContent: los nombres vienen de los celulares
  item.append(swatch, label);
  return item;
}

function fillList(id, rows) {
  $(id).replaceChildren(...rows.map((row) => listItem(row.text, row.color)));
}

export class Hud {
  setPhase(phase) {
    document.body.dataset.phase = phase;
  }

  setJoinUrl(url) {
    $("url").textContent = url;
  }

  setCount(count) {
    $("count").textContent = `${count} ${count === 1 ? "jugador" : "jugadores"}`;
  }

  showBoard(rows) {
    fillList("board-list", rows);
  }

  showPodium(podium) {
    fillList(
      "podium-list",
      podium.map((p) => ({ text: `${p.rank}. ${p.name}`, color: p.color })),
    );
  }
}
