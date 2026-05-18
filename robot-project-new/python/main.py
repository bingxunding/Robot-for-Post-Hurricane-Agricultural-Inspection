from config_loader import CONTROL_MODE

# ============================================================
# The running mode is selected by the "control_mode" field
# in input_data/map_config.json.
# To switch mode, modify this value in map_config.json:
#   "control_mode": "auto"
#       -> Run autonomous control mode.
#   "control_mode": "remote"
#       -> Run remote control mode.

print("Main Python file started.")
print("Selected control mode:", CONTROL_MODE)

if CONTROL_MODE == "auto":
    print("Starting autonomous control mode...")
    import auto_control

    auto_control.start()

elif CONTROL_MODE == "remote":
    print("Starting remote control mode...")
    import remote_control

    remote_control.start()

else:
    raise ValueError(f"Unknown control mode: {CONTROL_MODE}")