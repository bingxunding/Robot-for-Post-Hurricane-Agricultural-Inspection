function setStatus(text) {
    const statusEl = document.getElementById("status");
    if (statusEl) {
        statusEl.innerText = text;
    }
}

const socket = io(`http://${window.location.host}`, {
    transports: ["websocket", "polling"]
});

socket.on("connect", () => {
    setStatus("Connected");
});

socket.on("disconnect", () => {
    setStatus("Disconnected");
});

socket.on("debug", (msg) => {
    setStatus(msg.text);
});

function sendCommand(cmd) {
    setStatus("Hai premuto: " + cmd);
    socket.emit("move", { command: cmd });
}