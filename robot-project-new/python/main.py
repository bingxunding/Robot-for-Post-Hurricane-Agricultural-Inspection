from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import time
import threading

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

App.run()