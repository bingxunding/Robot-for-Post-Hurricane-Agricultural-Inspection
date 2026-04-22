from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

ui = WebUI()

def on_move(id, message):
    cmd = message.get("command")

    ui.send_message("debug", {"text": f"Python ha ricevuto: {cmd}"})

    try:
        if cmd == "forward":
            ui.send_message("debug", {"text": "Bridge: forward"})
            Bridge.call("move_forward")
        elif cmd == "backward":
            ui.send_message("debug", {"text": "Bridge: backward"})
            Bridge.call("move_backward")
        elif cmd == "left":
            ui.send_message("debug", {"text": "Bridge: left"})
            Bridge.call("turn_left")
        elif cmd == "right":
            ui.send_message("debug", {"text": "Bridge: right"})
            Bridge.call("turn_right")
        elif cmd == "stop":
            ui.send_message("debug", {"text": "Bridge: stop"})
            Bridge.call("stop_motors")
        else:
            raise ValueError(f"Unknown command: {cmd}")

    except Exception as e:
        ui.send_message("debug", {"text": f"Errore Python: {e}"})

ui.on_message("move", on_move)

App.run()