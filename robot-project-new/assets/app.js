function setStatus(text) {
    const statusEl = document.getElementById("status");
    if (statusEl) {
        statusEl.innerText = text;
    }
}

setStatus("JS caricato");

let socket = null;

try {
    if (typeof io === "undefined") {
        setStatus("ERRORE: io non definito");
    } else {
        setStatus("Socket.IO trovato");
        socket = io(`http://${window.location.host}`, {
            transports: ["websocket", "polling"]
        });

        socket.on("connect", () => {
            setStatus("Connected");
        });

        socket.on("disconnect", () => {
            setStatus("Disconnected");
        });

        socket.on("connect_error", (err) => {
            setStatus("Connect error");
            console.log("connect_error:", err);
        });

        socket.on("debug", (msg) => {
            setStatus(msg.text);
            alert(msg.text);
        });
    }
} catch (e) {
    setStatus("ERRORE JS");
    console.log(e);
}

function sendCommand(cmd) {
    setStatus("Hai premuto: " + cmd);

    if (!socket) {
        alert("Socket non inizializzato");
        return;
    }

    //alert("Comando inviato: " + cmd);
    socket.emit("move", { command: cmd });
}