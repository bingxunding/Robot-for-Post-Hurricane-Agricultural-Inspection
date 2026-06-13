from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import time
import threading
import requests

# --- Configurazione IP dell'ESP32 ---
ESP32_IP = "172.20.10.3"  # <- Sostituisci con l'IP che vedi nel Serial Monitor dell'ESP32

URL_FORWARD = f"http://{ESP32_IP}/forward"
URL_BACKWARD = f"http://{ESP32_IP}/backward"
URL_ROTATE_RIGHT = f"http://{ESP32_IP}/rotate_right"
URL_ROTATE_LEFT = f"http://{ESP32_IP}/rotate_left"
URL_TURN_RIGHT = f"http://{ESP32_IP}/turn_right"
URL_TURN_LEFT = f"http://{ESP32_IP}/turn_left"
URL_TURN_STOP = f"http://{ESP32_IP}/stop"

def send_command_to_ESP (url, command_name):
    """Invia il comando HTTP all'ESP32 e stampa la risposta."""
    try:
        print(f"Invio comando: {command_name} -> {url}")
        response = requests.get(url, timeout=5)
        print(f"Risposta ESP32: '{response.text}'")
        response.close()
    except requests.exceptions.RequestException as e:
        print(f"Errore: {e}")

def on_handshake_complete(msg):
    print("Handshake confirmed by Arduino")

Bridge.provide("handshake_complete", on_handshake_complete)


def printMovement(direction):
    print("You clicked: " + direction)

Bridge.provide("print_movement",printMovement)

def on_move(id, message):
    cmd = message.get("command")


    try:
        if cmd == "forward":
            ui.send_message("debug", {"text": "Bridge: forward"})
            Bridge.call("move_forward")
            send_command_to_ESP(URL_FORWARD, cmd)

        elif cmd == "backward":
            ui.send_message("debug", {"text": "Bridge: backward"})
            Bridge.call("move_backward")
            send_command_to_ESP(URL_BACKWARD, cmd)

        elif cmd == "left":
            ui.send_message("debug", {"text": "Bridge: left"})
            #Bridge.call("turn_left")
            Bridge.call("turn_left_slowly")
            send_command_to_ESP(URL_TURN_LEFT, cmd)

        elif cmd == "right":
            ui.send_message("debug", {"text": "Bridge: right"})
            #Bridge.call("turn_right")
            Bridge.call("turn_right_slowly")
            send_command_to_ESP(URL_TURN_RIGHT, cmd)

        elif cmd == "stop":
            ui.send_message("debug", {"text": "Bridge: stop"})
            Bridge.call("stop_motors")
            send_command_to_ESP(URL_TURN_STOP, cmd)

        elif cmd == "arm_down":
            ui.send_message("debug", {"text": "Bridge: arm down"})
            Bridge.call("setServoSpeed", 0)
        elif cmd == "arm_up":
            ui.send_message("debug", {"text": "Bridge: arm up"})
            Bridge.call("setServoSpeed", 180)    
        elif cmd == "arm_stop":
            ui.send_message("debug", {"text": "Bridge: arm stop"})
            Bridge.call("stopServoMotor")
        else:
            raise ValueError(f"Unknown command: {cmd}")

    except Exception as e:
        ui.send_message("debug", {"text": f"Errore Python: {e}"})
        
ui = WebUI()
ui.on_message("move", on_move)

def on_sonar_data1(msg):
    print("SONAR1:", msg)

def on_sonar_data2(msg):
    print("SONAR2:", msg)

def on_sonar_data3(msg):
    print("SONAR3:", msg)

Bridge.provide("sonar_data1", on_sonar_data1)
Bridge.provide("sonar_data2", on_sonar_data2)
Bridge.provide("sonar_data3", on_sonar_data3)

def start():
    print("Remote control Python file started.")
    App.run()