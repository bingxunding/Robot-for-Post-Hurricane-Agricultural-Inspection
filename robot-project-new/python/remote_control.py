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
URL_CURVATURE_PERCENTAGE = f"http://{ESP32_IP}/setcurvature"
URL_MOTORSPEED = f"http://{ESP32_IP}/setspeed"
CONNECTION_DELAY = 0.20

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
    return

def set_speed(msg):
    # Now Bridge is ready
    current_speed = Bridge.call("get_motor_speed")
    current_curve = Bridge.call("get_curvature")
    print(f"Current motor speed: {current_speed}")
    print(f"Current curvature: {current_curve}")
    
    try:
        requests.get(f"http://{ESP32_IP}/setspeed?value={current_speed}", timeout=2)
        requests.get(f"http://{ESP32_IP}/setcurvature?value={current_curve}", timeout=2)
        print(f"Synchronized ESP32: speed={current_speed}, curvature={current_curve}")
    except Exception as e:
        print(f"Failed to sync ESP32: {e}")

Bridge.provide("set_speed",set_speed)
Bridge.provide("handshake_complete", on_handshake_complete)

def printMovement(direction):
    print("You clicked: " + direction)

Bridge.provide("print_movement",printMovement)
    
def on_move(id, message):
    cmd = message.get("command")


    try:
        if cmd == "forward":
            ui.send_message("debug", {"text": "Bridge: forward"})
            print("MIAO")
            send_command_to_ESP(URL_FORWARD, cmd)
            threading.Timer(CONNECTION_DELAY, lambda: Bridge.call("move_forward")).start()

        elif cmd == "backward":
            ui.send_message("debug", {"text": "Bridge: backward"})
            send_command_to_ESP(URL_BACKWARD, cmd)
            threading.Timer(CONNECTION_DELAY, lambda: Bridge.call("move_backward")).start()
        elif cmd == "left":
            ui.send_message("debug", {"text": "Bridge: left"})
            #Bridge.call("turn_left")
            send_command_to_ESP(URL_TURN_LEFT, cmd)
            threading.Timer(CONNECTION_DELAY, lambda: Bridge.call("turn_left_slowly")).start()

        elif cmd == "right":
            ui.send_message("debug", {"text": "Bridge: right"})
            #Bridge.call("turn_right")
            send_command_to_ESP(URL_TURN_RIGHT, cmd)
            threading.Timer(CONNECTION_DELAY, lambda: Bridge.call("turn_right_slowly")).start()

        elif cmd == "stop":
            ui.send_message("debug", {"text": "Bridge: stop"})
            send_command_to_ESP(URL_TURN_STOP, cmd)
            threading.Timer(CONNECTION_DELAY, lambda: Bridge.call("stop_motors")).start()

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