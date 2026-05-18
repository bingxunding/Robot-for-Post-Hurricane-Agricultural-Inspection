import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "input_data",
    "map_config.json"
)

with open(CONFIG_FILE, "r") as file:
    config = json.load(file)

CONTROL_MODE = config["control_mode"]

COMMAND_FILE = os.path.join(
    BASE_DIR,
    config["command_file_path"]
)

STEP_FORWARD_TIME = config["step_forward_time"]
STEP_TURN_TIME = config["step_turn_time"]
STEP_STOP_TIME = config["step_stop_time"]
OBSTACLE_THRESHOLD_CM = config["obstacle_threshold_cm"]