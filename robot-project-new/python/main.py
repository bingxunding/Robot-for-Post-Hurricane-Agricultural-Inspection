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

def execute_command(command, steps):
    for i in range(steps):
        if command == "forward":
            Bridge.call("move_forward")
            time.sleep(0.5)
            Bridge.call("stop_motors")
            time.sleep(0.2)

        elif command == "backward":
            Bridge.call("move_backward")
            time.sleep(0.5)
            Bridge.call("stop_motors")
            time.sleep(0.2)

        elif command == "left":
            Bridge.call("turn_left")
            time.sleep(0.4)
            Bridge.call("stop_motors")
            time.sleep(0.2)

        elif command == "right":
            Bridge.call("turn_right")
            time.sleep(0.4)
            Bridge.call("stop_motors")
            time.sleep(0.2)

        elif command == "stop":
            Bridge.call("stop_motors")
            time.sleep(0.5)

def load_arduino_commands(command_file):
    commands = []

    with open(command_file, "r") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            command, steps = line.split(":")
            commands.append({
                "command": command,
                "steps": int(steps)
            })

    return commands

def run_autonomous_path(command_file):
    commands = load_arduino_commands(command_file)

    print("Autonomous path started.")
    print(f"Total commands: {len(commands)}")

    for item in commands:
        command = item["command"]
        steps = item["steps"]

        print(f"Executing: {command}:{steps}")

        execute_command(command, steps)

    Bridge.call("stop_motors")
    print("Autonomous path completed.")

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