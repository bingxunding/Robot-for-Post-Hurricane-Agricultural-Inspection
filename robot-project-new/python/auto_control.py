from arduino.app_utils import *
import time
import threading
import os

# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMMAND_FILE = os.path.join(
    BASE_DIR,
    "input_data",
    "arduino_commands.txt"
)

STEP_FORWARD_TIME = 0.5
STEP_TURN_TIME = 0.4
STEP_STOP_TIME = 0.2

# Obstacle avoidance configuration
obstacle_detected_flag = False

autonomous_started = False

# ============================================================
# Arduino callback functions
# ============================================================
def on_handshake_complete(msg):
    """
    This function is called when Arduino sketch.ino sends:
    Bridge.notify("handshake_complete", "arduino_ready");
    """

    global autonomous_started
    print("Handshake confirmed by Arduino")
    print("Arduino is ready.")
    if not autonomous_started:
        autonomous_started = True
        thread = threading.Thread(
            target=run_autonomous_path,
            daemon=True
        )
        thread.start()

Bridge.provide("handshake_complete", on_handshake_complete)


def printMovement(direction):
    """
    Receive movement feedback from sketch.ino.
    Example:
    Bridge.notify("print_movement", "forward");
    """

    print("Arduino movement:", direction)

Bridge.provide("print_movement", printMovement)

# ============================================================
# Sonar part
# ============================================================
def on_is_obstacle(msg):
    """
    Receive obstacle detection result from Arduino.
    Arduino sends:
    Bridge.notify("isObstacle", 1);  # obstacle detected
    Bridge.notify("isObstacle", 0);  # no obstacle
    """

    try:
        value = int(msg)
    except ValueError:
        print("Invalid obstacle message from Arduino:", msg)
        return
    
    global obstacle_detected_flag
    if value == 1:
        obstacle_detected_flag = True
        print("Obstacle detected by Arduino")
    elif value == 0:
        obstacle_detected_flag = False
        print("No obstacle detected by Arduino")
    else:
        print("Unknown obstacle state from Arduino:", msg)

Bridge.provide("isObstacle", on_is_obstacle)


# ============================================================
# Load command file
# ============================================================
def load_arduino_commands(command_file):
    """
    Load Arduino movement commands from arduino_commands.txt.
    Expected format:
    forward:5
    right:1
    forward:8
    left:1
    stop:1
    Return:
    [
        {"command": "forward", "steps": 5},
        {"command": "right", "steps": 1},
        ...
    ]
    """
    commands = []

    with open(command_file, "r") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            if ":" not in line:
                raise ValueError(
                    f"Invalid command format at line {line_number}: {line}"
                )

            command, steps = line.split(":")
            command = command.strip()
            steps = steps.strip()

            if not steps.isdigit():
                raise ValueError(
                    f"Invalid step number at line {line_number}: {line}"
                )

            commands.append({
                "command": command,
                "steps": int(steps)
            })

    return commands

# ============================================================
# Obstacle avoidance
# ============================================================
def obstacle_detected():
    return obstacle_detected_flag

def avoid_obstacle():
    """
    Simple local obstacle avoidance behavior.
    Strategy:
    stop
    turn right
    move forward a little
    turn left
    continue original path
    """
    print("Avoiding obstacle...")

    Bridge.call("stop_motors")
    time.sleep(0.3)

    Bridge.call("turn_right")
    time.sleep(STEP_TURN_TIME)
    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    Bridge.call("move_forward")
    time.sleep(STEP_FORWARD_TIME)
    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    Bridge.call("turn_left")
    time.sleep(STEP_TURN_TIME)
    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    print("Obstacle avoidance completed.")

# ============================================================
# Execute movement command
# ============================================================
def execute_command(command, steps):
    """
    Execute one command using Bridge.call().
    Example:
    forward:3
    Means:
    move_forward -> stop
    move_forward -> stop
    move_forward -> stop
    """
    for i in range(steps):
        print(f"Step {i + 1}/{steps}: {command}")
        if command == "forward":
            if obstacle_detected():
                avoid_obstacle()
                continue

            Bridge.call("move_forward")
            time.sleep(STEP_FORWARD_TIME)     # Unit: second, stop the motor after running for 0.5s

            Bridge.call("stop_motors")       # Without this, the motor will keep rotating.
            time.sleep(STEP_STOP_TIME)

        elif command == "backward":
            Bridge.call("move_backward")
            time.sleep(STEP_FORWARD_TIME)

            Bridge.call("stop_motors")
            time.sleep(STEP_STOP_TIME)

        elif command == "left":
            Bridge.call("turn_left")
            time.sleep(STEP_TURN_TIME)

            Bridge.call("stop_motors")
            time.sleep(STEP_STOP_TIME)

        elif command == "right":
            Bridge.call("turn_right")
            time.sleep(STEP_TURN_TIME)

            Bridge.call("stop_motors")
            time.sleep(STEP_STOP_TIME)

        elif command == "stop":
            Bridge.call("stop_motors")
            time.sleep(0.5)

        else:
            print(f"Unknown command: {command}")

# ============================================================
# Run autonomous path
# ============================================================
def run_autonomous_path():
    """
    Main autonomous control logic.
    It reads arduino_commands.txt and sends movement commands to sketch.ino.
    """
    print("====================================")
    print("Autonomous control started")
    print("====================================")

    if not os.path.exists(COMMAND_FILE):
        print(f"Command file not found: {COMMAND_FILE}")
        Bridge.call("stop_motors")
        return

    try:
        commands = load_arduino_commands(COMMAND_FILE)

        print(f"Command file loaded successfully.")
        print(f"Command file path: {COMMAND_FILE}")
        print(f"Total commands: {len(commands)}")

        print("First 10 commands:")
        for item in commands[:10]:
            print(item)

        print("====================================")
        print("Executing autonomous path")
        print("====================================")

        for item in commands:
            command = item["command"]
            steps = item["steps"]

            print(f"\nExecuting command: {command}:{steps}")
            execute_command(command, steps)

        Bridge.call("stop_motors")

        print("\n====================================")
        print("Autonomous path completed")
        print("====================================")

    except Exception as e:
        print(f"Autonomous control error: {e}")
        Bridge.call("stop_motors")

# ============================================================
# App entry
# ============================================================
def start():
    print("Auto control Python file started.")
    print("Waiting for Arduino handshake...")
    App.run()