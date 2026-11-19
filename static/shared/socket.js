export function connect(path, onMessage, onOpen = () => {}) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  let ws;

  const open = () => {
    ws = new WebSocket(`${protocol}://${location.host}${path}`);
    ws.onopen = onOpen;
    ws.onmessage = (event) => onMessage(JSON.parse(event.data));
    ws.onclose = () => setTimeout(open, 1000);
  };
  open();

  return {
    send(message) {
      const ready = ws?.readyState === WebSocket.OPEN;
      if (ready) ws.send(JSON.stringify(message));
      return ready;
    },
  };
}
