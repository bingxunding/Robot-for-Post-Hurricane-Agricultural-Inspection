import cv2
import math
import json
import os


def load_base_map_config(config_path):
    """
    Load base map configuration from JSON file.

    The JSON file must already exist and contain these required fields:
    - image_path
    - real_scale_bar_m
    - robot_width_m
    - safety_margin_m
    """

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please create map_config.json first with these fields:\n"
            "{\n"
            '    "image_path": "pathGeneration/env-extra.jpg",\n'
            '    "real_scale_bar_m": 30,\n'
            '    "robot_width_m": 0.4,\n'
            '    "safety_margin_m": 0.2\n'
            "}"
        )

    with open(config_path, "r") as file:
        config = json.load(file)

    required_fields = [
        "image_path",
        "real_scale_bar_m",
        "robot_width_m",
        "safety_margin_m"
    ]

    missing_fields = []

    for field in required_fields:
        if field not in config:
            missing_fields.append(field)

    if missing_fields:
        raise KeyError(
            f"Missing required fields in {config_path}: {missing_fields}\n"
            "The initial map_config.json must contain:\n"
            "- image_path\n"
            "- real_scale_bar_m\n"
            "- robot_width_m\n"
            "- safety_margin_m"
        )

    return config


def calculate_map_config_from_scale_bar(config_path):
    """
    Read base map configuration from JSON file.

    The user clicks the two endpoints of the scale bar in the image.
    Then this function calculates:
    - scale_bar_pixels
    - pixels_per_meter
    - meters_per_pixel
    - inflation_radius_m
    - inflation_radius_pixels
    - scale_bar_point_1
    - scale_bar_point_2

    If these computed fields already exist in the JSON file,
    they will be overwritten.
    """

    config = load_base_map_config(config_path)

    image_path = config["image_path"]
    real_scale_bar_m = config["real_scale_bar_m"]
    robot_width_m = config["robot_width_m"]
    safety_margin_m = config["safety_margin_m"]

    points = []

    img = cv2.imread(image_path)

    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    display_img = img.copy()

    def click_event(event, x, y, flags, param):
        nonlocal display_img, config

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) >= 2:
                print("Already selected two points. Press ESC to exit.")
                return

            points.append((x, y))
            print(f"Point {len(points)}: ({x}, {y})")

            cv2.circle(display_img, (x, y), 5, (0, 0, 255), -1)

            if len(points) == 2:
                cv2.line(display_img, points[0], points[1], (0, 255, 255), 2)

                dx = points[1][0] - points[0][0]
                dy = points[1][1] - points[0][1]

                scale_bar_pixels = math.sqrt(dx * dx + dy * dy)

                pixels_per_meter = scale_bar_pixels / real_scale_bar_m
                meters_per_pixel = real_scale_bar_m / scale_bar_pixels

                inflation_radius_m = robot_width_m / 2 + safety_margin_m

                inflation_radius_pixels = math.ceil(
                    inflation_radius_m * pixels_per_meter
                )

                # These fields will overwrite old values if they already exist
                computed_config = {
                    "scale_bar_pixels": scale_bar_pixels,
                    "pixels_per_meter": pixels_per_meter,
                    "meters_per_pixel": meters_per_pixel,
                    "inflation_radius_m": inflation_radius_m,
                    "inflation_radius_pixels": inflation_radius_pixels,
                    "scale_bar_point_1": {
                        "x": points[0][0],
                        "y": points[0][1]
                    },
                    "scale_bar_point_2": {
                        "x": points[1][0],
                        "y": points[1][1]
                    }
                }

                config.update(computed_config)

                with open(config_path, "w") as file:
                    json.dump(config, file, indent=4)

                print("================================")
                print("Base configuration:")
                print(f"Image path: {image_path}")
                print(f"Real scale bar length: {real_scale_bar_m:.2f} m")
                print(f"Robot width: {robot_width_m:.2f} m")
                print(f"Safety margin: {safety_margin_m:.2f} m")
                print("--------------------------------")
                print("Computed configuration:")
                print(f"Scale bar pixel length: {scale_bar_pixels:.2f} px")
                print(f"Pixels per meter: {pixels_per_meter:.4f} px/m")
                print(f"Meters per pixel: {meters_per_pixel:.4f} m/px")
                print(f"Inflation radius: {inflation_radius_m:.2f} m")
                print(f"Inflation radius: {inflation_radius_pixels} px")
                print("--------------------------------")
                print(f"Configuration updated: {config_path}")
                print("================================")

            cv2.imshow("Click scale bar endpoints", display_img)

    cv2.imshow("Click scale bar endpoints", display_img)
    cv2.setMouseCallback("Click scale bar endpoints", click_event)

    print("Click the two endpoints of the scale bar.")
    print("Press ESC to exit after selecting two points.")

    while True:
        key = cv2.waitKey(1)

        # Press ESC to exit manually
        if key == 27:
            break

        # Automatically close after two points are selected
        if len(points) == 2:
            cv2.waitKey(1000)
            break

    cv2.destroyAllWindows()

    if len(points) < 2:
        raise ValueError("You must click two endpoints of the scale bar.")


if __name__ == "__main__":
    CONFIG_PATH = "output_preprocessing/map_config.json"

    calculate_map_config_from_scale_bar(
        config_path=CONFIG_PATH
    )