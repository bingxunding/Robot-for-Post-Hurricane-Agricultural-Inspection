from arduino.app_utils import *
import time
import threading
import os
import numpy as np
import math
import requests

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

TURN_TIMEOUT = 5.0
USE_IMU = True
# One forward/backward step target distance.
# From map scale:
# meters_per_pixel = 0.08063467359130036
# pixels_per_step = 10
# 10 * 0.08063467359130036 = 0.8063467359130036 m
MOVE_DISTANCE_PER_STEP = 0.8063467359130036

# Safety timeout for one forward/backward movement
MOVE_TIMEOUT = 3.0

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

    if USE_IMU:
        turn_right_by_angle(45)
    else:
        Bridge.call("turn_right")
        time.sleep(STEP_TURN_TIME)
        Bridge.call("stop_motors")
        time.sleep(STEP_STOP_TIME)

    Bridge.call("move_forward")
    time.sleep(STEP_FORWARD_TIME)
    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    if USE_IMU:
        turn_left_by_angle(45)
    else:
        Bridge.call("turn_left")
        time.sleep(STEP_TURN_TIME)
        Bridge.call("stop_motors")
        time.sleep(STEP_STOP_TIME)

    print("Obstacle avoidance completed.")

# ============================================================
# IMU
# ============================================================
current_yaw_deg = 0.0
last_gyro_z = 0.0
imu_lock = threading.Lock()
TURN_ANGLE_PER_STEP = 90
current_displacement = 0.0

def reset_yaw():
    global current_yaw_deg

    with imu_lock:
        current_yaw_deg = 0.0


def get_yaw():
    with imu_lock:
        return current_yaw_deg

def reset_motion_estimation():
    """
    Reset velocity and displacement estimation before each forward/backward step.
    """
    global CURRENT_VELOCITY
    global current_displacement

    with imu_lock:
        CURRENT_VELOCITY = 0.0
        current_displacement = 0.0

def get_displacement():
    """
    Return current estimated displacement.
    """
    with imu_lock:
        return current_displacement

def update_yaw_from_gyro(gyro_z):
    global current_yaw_deg
    global last_gyro_z

    delta_yaw_rad = gyro_z * FREQUENCY_IMU_DATA
    delta_yaw_deg = math.degrees(delta_yaw_rad)

    with imu_lock:
        current_yaw_deg += delta_yaw_deg
        last_gyro_z = gyro_z

def update_displacement_from_accel(acc_y):
    """
    Estimate forward/backward displacement from Y-axis acceleration.

    acc_y is expected to be in m/s^2.
    FREQUENCY_IMU_DATA is the sampling interval in seconds.

    This is a simple integration:
    delta_s = v * dt + 0.5 * a * dt^2
    v = v + a * dt
    """
    global CURRENT_VELOCITY
    global current_displacement

    dt = FREQUENCY_IMU_DATA

    with imu_lock:
        delta_s = CURRENT_VELOCITY * dt + 0.5 * acc_y * dt * dt
        CURRENT_VELOCITY += acc_y * dt
        current_displacement += delta_s

def turn_right_by_angle(target_angle_deg=90):
    print(f"Turning right by IMU angle: {target_angle_deg} degrees")

    reset_yaw()

    Bridge.call("turn_right")
    send_command_to_ESP(URL_ROTATE_RIGHT, "rotate_right")

    start_time = time.time()

    while abs(get_yaw()) < target_angle_deg:
        if time.time() - start_time > TURN_TIMEOUT:
            print("Turn right timeout. Stopping motors.")
            break
        time.sleep(0.02)

    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    print("Right turn completed. Final yaw:", get_yaw())


def turn_left_by_angle(target_angle_deg=90):
    print(f"Turning left by IMU angle: {target_angle_deg} degrees")

    reset_yaw()

    Bridge.call("turn_left")
    send_command_to_ESP(URL_ROTATE_LEFT, "rotate_left")

    start_time = time.time()

    while abs(get_yaw()) < target_angle_deg:
        if time.time() - start_time > TURN_TIMEOUT:
            print("Turn left timeout. Stopping motors.")
            break
        time.sleep(0.02)

    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    print("Left turn completed. Final yaw:", get_yaw())

def move_forward_by_distance(target_distance=MOVE_DISTANCE_PER_STEP):
    """
    Move forward until the IMU-estimated displacement reaches target_distance.
    This is an IMU-assisted movement, with timeout protection.
    """
    print(f"Moving forward by IMU distance: {target_distance} m")

    reset_motion_estimation()

    Bridge.call("move_forward")
    send_command_to_ESP(URL_FORWARD, "forward")

    start_time = time.time()

    while abs(get_displacement()) < target_distance:
        if obstacle_detected():
            print("Obstacle detected during IMU forward movement.")
            break

        if time.time() - start_time > MOVE_TIMEOUT:
            print("Forward movement timeout. Stopping motors.")
            break

        time.sleep(0.02)

    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    print("Forward movement completed. Estimated displacement:", get_displacement())

def move_backward_by_distance(target_distance=MOVE_DISTANCE_PER_STEP):
    """
    Move backward until the IMU-estimated displacement reaches target_distance.
    This is an IMU-assisted movement, with timeout protection.
    """
    print(f"Moving backward by IMU distance: {target_distance} m")

    reset_motion_estimation()

    Bridge.call("move_backward")
    send_command_to_ESP(URL_BACKWARD, "backward")

    start_time = time.time()

    while abs(get_displacement()) < target_distance:
        if time.time() - start_time > MOVE_TIMEOUT:
            print("Backward movement timeout. Stopping motors.")
            break

        time.sleep(0.02)

    Bridge.call("stop_motors")
    time.sleep(STEP_STOP_TIME)

    print("Backward movement completed. Estimated displacement:", get_displacement())

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
            if USE_IMU:
                move_forward_by_distance(MOVE_DISTANCE_PER_STEP)
            else:
                Bridge.call("move_forward")
                time.sleep(STEP_FORWARD_TIME)
                Bridge.call("stop_motors")
                time.sleep(STEP_STOP_TIME)

        elif command == "backward":
            if USE_IMU:
                move_backward_by_distance(MOVE_DISTANCE_PER_STEP)
            else:
                Bridge.call("move_backward")
                time.sleep(STEP_FORWARD_TIME)
                Bridge.call("stop_motors")
                time.sleep(STEP_STOP_TIME)

        elif command == "left":
            if USE_IMU:
                turn_left_by_angle(TURN_ANGLE_PER_STEP)
            else:
                Bridge.call("turn_left")
                time.sleep(STEP_TURN_TIME)
                Bridge.call("stop_motors")
                time.sleep(STEP_STOP_TIME)

        elif command == "right":
            if USE_IMU:
                turn_right_by_angle(TURN_ANGLE_PER_STEP)
            else:
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
    global USE_IMU
    calibration_start_time = time.time()
    calibration_timeout = 30
    while not CALIBRATED:
        print("Waiting for IMU calibration before autonomous path...")
        if time.time() - calibration_start_time > calibration_timeout:
            print("IMU calibration timeout. Starting with time-based turning fallback.")
            USE_IMU = False
            break
        time.sleep(1)

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


FREQUENCY_IMU_DATA = 0.5 # if you modify this, also modify the sketch parameter
CURRENT_VELOCITY = 0
CALIBRATION_N = 100
DEADBAND_K = 1.5
CALIBRATED = False
GYRO_BATCH = []
ACCEL_BATCH = []
GYRO_BIASES = [0,0,0]
ACCEL_BIASES = [0,0,0]
GYRO_STDS = [0,0,0]
ACCEL_STDS = [0,0,0]
FORWARD_INCLINATION = 0 #angle
#assuming starting position is 0
ANGLE_IN_RESPECT_STARTING_POS = 0 #<--rotation value you need

#gyro_values = [x,y,z], after the filter, so no need for biases and stds
def modify_inclination(gyro_values):
    global FORWARD_INCLINATION
    global ANGLE_IN_RESPECT_STARTING_POS
    
    delta_angle_x = gyro_values[0] * FREQUENCY_IMU_DATA
    delta_angle_y = gyro_values[1] * FREQUENCY_IMU_DATA
    delta_angle_z = gyro_values[2] * FREQUENCY_IMU_DATA

    FORWARD_INCLINATION = FORWARD_INCLINATION + delta_angle_y
    ANGLE_IN_RESPECT_STARTING_POS = ANGLE_IN_RESPECT_STARTING_POS + delta_angle_z
    
    return [delta_angle_x,delta_angle_y,delta_angle_z]

#this calculates the space I moved forward
def calculate_delta_forward_movement(acc_y):
    delta_movement = CURRENT_VELOCITY * FORWARD_INCLINATION * FREQUENCY_IMU_DATA 
    return delta_movement #<---space you need
    
#assuming I get N reading, in the function calculate the average min values and use it as min
#valid values
#gyro_values are [[x,y,z],[x,y,z]]
def calibrate(gyro_values,acc_values):
    gyro_x = []
    gyro_y = []
    gyro_z = []
    acc_x = []
    acc_y = []
    acc_z = []
    for values in gyro_values:
        gyro_x.append(values[0])
        gyro_y.append(values[1])
        gyro_z.append(values[2])
    
    for values in acc_values:
        acc_x.append(values[0])
        acc_y.append(values[1])
        acc_z.append(values[2])

    avg_gyro_X = sum(gyro_x)/len(gyro_x)
    avg_gyro_Y = sum(gyro_y)/len(gyro_y)
    avg_gyro_Z = sum(gyro_z)/len(gyro_z)
    avg_acc_X = sum(acc_x)/len(acc_x)
    avg_acc_Y = sum(acc_y)/len(acc_y)
    avg_acc_Z = sum(acc_z)/len(acc_z)
    gyro_biases = [avg_gyro_X, avg_gyro_Y, avg_gyro_Z]
    acc_biases = [avg_acc_X,avg_acc_Y, avg_acc_Z]

    # Sample standard deviation (default ddof=0 for population)
    gyro_x_std = float(np.std(gyro_x, ddof=1))
    gyro_y_std = float(np.std(gyro_y, ddof=1))
    gyro_z_std = float(np.std(gyro_z, ddof=1))
    acc_x_std = float(np.std(acc_x, ddof=1))
    acc_y_std = float(np.std(acc_y, ddof=1))
    acc_z_std = float(np.std(acc_z, ddof=1))
    
    gyro_std = [gyro_x_std,gyro_y_std,gyro_z_std]
    acc_std = [acc_x_std, acc_y_std, acc_z_std]
    

    return gyro_biases, acc_biases, gyro_std, acc_std

def filter(raw_accel, raw_gyro):
    a_x = raw_accel[0] - ACCEL_BIASES[0]
    a_y = raw_accel[1] - ACCEL_BIASES[1]
    a_z = raw_accel[2] - ACCEL_BIASES[2]
    
    g_x = raw_gyro[0] - GYRO_BIASES[0]
    g_y = raw_gyro[1] - GYRO_BIASES[1]
    g_z = raw_gyro[2] - GYRO_BIASES[2]
    
    # Apply deadband to each scalar component
    if abs(a_x) < DEADBAND_K * ACCEL_STDS[0]:
        a_x = 0
    if abs(a_y) < DEADBAND_K * ACCEL_STDS[1]:
        a_y = 0
    if abs(a_z) < DEADBAND_K * ACCEL_STDS[2]:
        a_z = 0
    
    if abs(g_x) < DEADBAND_K * GYRO_STDS[0]:
        g_x = 0
    if abs(g_y) < DEADBAND_K * GYRO_STDS[1]:
        g_y = 0
    if abs(g_z) < DEADBAND_K * GYRO_STDS[2]:
        g_z = 0

    return [a_x, a_y, a_z], [g_x, g_y, g_z]
    
def parseIMUdata(string):

    data = string.strip().strip(',')
    
    # Split by comma into list of strings
    values = data.split(',')
    
    # Convert to floats
    if len(values) >= 6:
        accel_x = float(values[0])
        accel_y = float(values[1])
        accel_z = float(values[2])
        gyro_x = float(values[3])
        gyro_y = float(values[4])
        gyro_z = float(values[5])
        
        return [accel_x,accel_y,accel_z], [gyro_x, gyro_y,gyro_z]
        
    else:
        return None
        
def getIMU(text):
    global CURRENT_VELOCITY
    global CALIBRATED
    global GYRO_BATCH
    global ACCEL_BATCH
    global GYRO_BIASES
    global ACCEL_BIASES
    global GYRO_STDS
    global ACCEL_STDS

    if CALIBRATED:
        parsed_data = parseIMUdata(text)
        if parsed_data is None:
            print("Invalid IMU data:", text)
            return
        
        acc1Y=parsed_data[0][1]
        print("pre filter accelY "+str(acc1Y))
        
        filtered_data = filter(parsed_data[0],parsed_data[1])
        print("\n")
        accY=filtered_data[0][1]
        
        print("pre_angle calculation delta: " + str(CURRENT_VELOCITY*FREQUENCY_IMU_DATA) +"\n")
        delta_movement = calculate_delta_forward_movement(accY)
        print("after angle calculation delta: " + str(delta_movement) +"\n")
        
        print("accelY "+str(accY))
        # Update velocity and displacement using acceleration
        update_displacement_from_accel(accY)
        print("current velocity: " + str(CURRENT_VELOCITY))
        print("")
        print("\n")

        print("current inclination: " + str(FORWARD_INCLINATION) +"\n")
        print("gyro values:\n")
        print(filtered_data[1])
        modify_inclination(filtered_data[1])
        # Use gyro_z to update yaw angle for IMU-based turning
        update_yaw_from_gyro(filtered_data[1][2])
        print("updated inclination: " + str(FORWARD_INCLINATION) +"\n")
        
    else:
        print("Calibrating..." + str(len(GYRO_BATCH)))
        if (len(GYRO_BATCH) < CALIBRATION_N):
            accel_batch, gyro_batch = parseIMUdata(text)
            ACCEL_BATCH.append(accel_batch)
            GYRO_BATCH.append(gyro_batch)
        else:
            print("Finished calibrating")
            CALIBRATED = True
            GYRO_BIASES, ACCEL_BIASES, GYRO_STDS, ACCEL_STDS = calibrate(GYRO_BATCH, ACCEL_BATCH)
            print(GYRO_BIASES)
            print("\n")
            print(ACCEL_BIASES)
            print("\n")
            print(GYRO_STDS)
            print("\n")
            print(ACCEL_STDS)
            print("\n")

Bridge.provide("get_imu",getIMU)

# ============================================================
# App entry
# ============================================================
def start():
    print("Auto control Python file started.")
    print("Waiting for Arduino handshake...")
    App.run()