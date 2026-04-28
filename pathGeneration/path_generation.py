import cv2
import numpy as np
import matplotlib.pyplot as plt
import os


def show_and_save(title, image, output_dir):
    """
    Show and save intermediate image results.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save image
    filename = title.lower().replace(" ", "_") + ".png"
    path = os.path.join(output_dir, filename)

    if len(image.shape) == 2:
        cv2.imwrite(path, image)
        plt.imshow(image, cmap="gray")
    else:
        cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        plt.imshow(image)

    plt.title(title)
    plt.axis("off")
    plt.show()


def show_comparison(original_image, processed_image, output_dir):
    """
    Show original image and processed binary map side by side.
    """
    os.makedirs(output_dir, exist_ok=True)

    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.imshow(original_image)
    plt.title("Original Resized Image")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(processed_image, cmap="gray")
    plt.title("Cleaned Binary Map")
    plt.axis("off")

    plt.tight_layout()

    comparison_path = os.path.join(output_dir, "comparison_original_vs_binary.png")
    plt.savefig(comparison_path, dpi=300)

    plt.show()


def preprocess_real_environment_image(
    image_path,
    output_dir="output_preprocessing",
    resize_width=800,
    blur_kernel=5,
    threshold_value=120,
    use_canny=False,
    use_hsv_correction=True
):
    """
    Preprocess a real environment image and generate a binary map.

    White pixels = traversable area
    Black pixels = obstacle / non-traversable area
    """

    # 1. Read image
    original_bgr = cv2.imread(image_path)

    if original_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    # Convert BGR to RGB for displaying
    # For the beginning OpenCV read the pic is BGR
    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

    # 2. Resize image for easier processing
    height, width = original_rgb.shape[:2]
    scale = resize_width / width
    new_height = int(height * scale)
    resized_rgb = cv2.resize(original_rgb, (resize_width, new_height))

    # 3. Convert to grayscale
    gray = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2GRAY)
    # show_and_save("02 Grayscale Image", gray, output_dir)

    # 4. Noise reduction using Gaussian Blur
    # sure blur_kernel is odd number
    # OpenCV's GaussianBlur() requires the kernel size to be an odd number
    if blur_kernel % 2 == 0:
        blur_kernel += 1

    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    # show_and_save("03 Gaussian Blur", blurred, output_dir)

    # 5. Threshold or Canny edge detection
    if use_canny:
        edges = cv2.Canny(blurred, 50, 150)
        # show_and_save("04 Canny Edge Detection", edges, output_dir)

        # Invert edges to create a rough traversable map
        binary_map = cv2.bitwise_not(edges)

    else:
        # Binary threshold
        # Pixels brighter than threshold_value become white
        # Pixels darker than threshold_value become black
        _, binary_map = cv2.threshold(
            blurred,
            threshold_value,
            255,
            cv2.THRESH_BINARY
        )
        # show_and_save("04 Binary Threshold Map", binary_map, output_dir)

    # 5.1 HSV-based traversable area detection for satellite images
    if use_hsv_correction:
        hsv = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2HSV)

        # Green areas: grass / vegetation / open ground
        lower_green = np.array([30, 20, 30])
        upper_green = np.array([95, 255, 240])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)

        # Brown / yellow areas: soil, dirt path, dry grass
        lower_brown = np.array([5, 15, 40])
        upper_brown = np.array([40, 220, 240])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)

        # Light open ground: pale soil / dry grass / open area
        lower_light_ground = np.array([15, 5, 100])
        upper_light_ground = np.array([45, 130, 255])
        light_ground_mask = cv2.inRange(hsv, lower_light_ground, upper_light_ground)

        # Combine traversable areas
        traversable_mask = cv2.bitwise_or(green_mask, brown_mask)
        traversable_mask = cv2.bitwise_or(traversable_mask, light_ground_mask)

        # Bright + low saturation = roofs / concrete / buildings
        lower_roof = np.array([0, 0, 150])
        upper_roof = np.array([180, 70, 255])
        roof_mask = cv2.inRange(hsv, lower_roof, upper_roof)

        # Very dark regions = tree shadows / dense obstacles
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([180, 255, 35])
        dark_mask = cv2.inRange(hsv, lower_dark, upper_dark)

        # Blue map marker / UI elements
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Combine obstacle masks
        obstacle_mask = cv2.bitwise_or(roof_mask, dark_mask)
        obstacle_mask = cv2.bitwise_or(obstacle_mask, blue_mask)

        # Remove obstacle areas from traversable area
        traversable_mask[obstacle_mask == 255] = 0

        # Use HSV result as the final binary map
        # White = traversable, black = obstacle
        binary_map = traversable_mask

    # 6. Morphological processing
    # Remove small noise and fill small holes
    kernel = np.ones((5, 5), np.uint8)

    opened = cv2.morphologyEx(binary_map, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    # Show original image and processed binary map together
    show_comparison(resized_rgb, closed, output_dir)

    # 7. Convert to occupancy grid
    # 0 = free space, 1 = obstacle
    # Here: white = free space, black = obstacle
    occupancy_grid = np.where(closed == 255, 0, 1)

    # Save as NumPy binary file
    np.save(os.path.join(output_dir, "occupancy_grid.npy"), occupancy_grid)

    # Save as readable txt file
    # np.savetxt(
    #     os.path.join(output_dir, "occupancy_grid.txt"),
    #     occupancy_grid,
    #     fmt="%d"
    # )

    print("Preprocessing completed.")
    print(f"Binary map saved in: {output_dir}")
    print(f"Occupancy grid shape: {occupancy_grid.shape}")
    print("White = free space, Black = obstacle")

    return closed, occupancy_grid


if __name__ == "__main__":
    image_path = "pathGeneration/env.jpg"

    binary_map, occupancy_grid = preprocess_real_environment_image(
        image_path=image_path,
        output_dir="output_preprocessing",
        resize_width=800,
        blur_kernel=5,
        threshold_value=120,
        use_canny=False,
        use_hsv_correction=True
    )