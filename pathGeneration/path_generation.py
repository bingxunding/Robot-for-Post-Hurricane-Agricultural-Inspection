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


def preprocess_real_environment_image(
    image_path,
    output_dir="output_preprocessing",
    resize_width=800,
    blur_kernel=5,
    threshold_value=120,
    use_canny=False
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

    #show_and_save("01 Original Resized Image", resized_rgb, output_dir)

    # 3. Convert to grayscale
    gray = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2GRAY)
    #show_and_save("02 Grayscale Image", gray, output_dir)

    # 4. Noise reduction using Gaussian Blur
    # sure blur_kernel is odd number
    # OpenCV's GaussianBlur() requires the kernel size to be an odd number
    if blur_kernel % 2 == 0:
        blur_kernel += 1

    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
    #show_and_save("03 Gaussian Blur", blurred, output_dir)

    # 5. Threshold or Canny edge detection
    if use_canny:
        edges = cv2.Canny(blurred, 50, 150)
        #show_and_save("04 Canny Edge Detection", edges, output_dir)

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
        #show_and_save("04 Binary Threshold Map", binary_map, output_dir)

    # 6. Morphological processing
    # Remove small noise and fill small holes
    kernel = np.ones((5, 5), np.uint8)

    opened = cv2.morphologyEx(binary_map, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    show_and_save("05 Cleaned Binary Map", closed, output_dir)

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
        use_canny=False
    )