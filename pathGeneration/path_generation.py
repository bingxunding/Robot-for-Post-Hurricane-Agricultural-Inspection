import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import heapq
import random


def show_and_save(title, image, output_dir):
    """
    Show and save intermediate image results.
    """
    os.makedirs(output_dir, exist_ok=True)

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
    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

    # 2. Resize image for easier processing
    height, width = original_rgb.shape[:2]
    scale = resize_width / width
    new_height = int(height * scale)
    resized_rgb = cv2.resize(original_rgb, (resize_width, new_height))

    # 3. Convert to grayscale
    gray = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2GRAY)

    # 4. Noise reduction using Gaussian Blur
    if blur_kernel % 2 == 0:
        blur_kernel += 1

    blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

    # 5. Threshold or Canny edge detection
    if use_canny:
        edges = cv2.Canny(blurred, 50, 150)

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

    print("Preprocessing completed.")
    print(f"Binary map saved in: {output_dir}")
    print(f"Occupancy grid shape: {occupancy_grid.shape}")
    print("White = free space, Black = obstacle")
    print("0 = free space, 1 = obstacle")

    return closed, occupancy_grid


def keep_largest_free_component(occupancy_grid):
    """
    Keep only the largest connected free-space component.

    occupancy_grid:
    0 = free space
    1 = obstacle

    Return:
    - largest_component_grid:
      0 = largest free space
      1 = obstacle or other disconnected free areas

    - largest_free_mask:
      255 = largest free space
      0 = obstacle
    """

    # Free space mask: 255 = free, 0 = obstacle
    free_mask = np.where(occupancy_grid == 0, 255, 0).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        free_mask,
        connectivity=8
    )

    if num_labels <= 1:
        raise ValueError("No connected free-space component found.")

    # label 0 is background, so ignore it
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])

    largest_free_mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)

    # Convert back to occupancy grid
    # 0 = free space, 1 = obstacle
    largest_component_grid = np.where(largest_free_mask == 255, 0, 1)

    return largest_component_grid, largest_free_mask


def astar(occupancy_grid, start, target):
    """
    A* path planning on occupancy grid.

    start and target format:
    (x, y)

    occupancy_grid:
    0 = free space
    1 = obstacle
    """

    height, width = occupancy_grid.shape

    def heuristic(a, b):
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def is_valid(point):
        x, y = point
        return (
            0 <= x < width
            and 0 <= y < height
            and occupancy_grid[y, x] == 0
        )

    if not is_valid(start):
        raise ValueError(f"Start point {start} is not in free space.")

    if not is_valid(target):
        raise ValueError(f"Target point {target} is not in free space.")

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    # 8-direction movement: horizontal, vertical, and diagonal
    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1)
    ]

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == target:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            return path

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)

            if not is_valid(neighbor):
                continue

            # Diagonal movement cost is slightly higher
            if dx != 0 and dy != 0:
                move_cost = 1.414
            else:
                move_cost = 1

            tentative_g_score = g_score[current] + move_cost

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score

                f_score = tentative_g_score + heuristic(neighbor, target)
                heapq.heappush(open_set, (f_score, neighbor))

    return []


def plan_path_through_points(occupancy_grid, start_point, inspection_points):
    """
    Plan path from start point through multiple inspection points.

    Points are visited in the given order.
    """

    full_path = []
    current_point = start_point

    for target_point in inspection_points:
        path_segment = astar(occupancy_grid, current_point, target_point)

        if not path_segment:
            raise ValueError(f"No path found from {current_point} to {target_point}")

        # Avoid duplicate point when connecting path segments
        if full_path:
            full_path.extend(path_segment[1:])
        else:
            full_path.extend(path_segment)

        current_point = target_point

    return full_path


def find_top_left_free_point(occupancy_grid):
    """
    Find the top-left free point in the occupancy grid.

    Return format:
    (x, y)
    """

    height, width = occupancy_grid.shape

    for y in range(height):
        for x in range(width):
            if occupancy_grid[y, x] == 0:
                return (x, y)

    raise ValueError("No free space found in occupancy grid.")


def find_bottom_right_free_point(occupancy_grid):
    """
    Find the bottom-right free point in the occupancy grid.

    Return format:
    (x, y)
    """

    height, width = occupancy_grid.shape

    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            if occupancy_grid[y, x] == 0:
                return (x, y)

    raise ValueError("No free space found in occupancy grid.")


def select_random_inspection_points_from_path(path, number_of_points=3):
    """
    Select random inspection points from an existing feasible path.

    This ensures all inspection points are on free space.
    """

    if len(path) <= 2:
        raise ValueError("Path is too short to select inspection points.")

    # Exclude start and target
    candidate_points = path[1:-1]

    if number_of_points > len(candidate_points):
        number_of_points = len(candidate_points)

    selected_points = random.sample(candidate_points, number_of_points)

    # Sort points according to their order in the original path
    selected_points.sort(key=lambda p: path.index(p))

    return selected_points


def show_path_on_map(binary_map, path, start_point, inspection_points, output_dir):
    """
    Show planned path on the cleaned binary map.
    """

    os.makedirs(output_dir, exist_ok=True)

    path_image = cv2.cvtColor(binary_map, cv2.COLOR_GRAY2RGB)

    # Draw path in red
    for x, y in path:
        path_image[y, x] = [255, 0, 0]

    # Draw start point in blue
    sx, sy = start_point
    cv2.circle(path_image, (sx, sy), 5, (0, 0, 255), -1)

    # Draw inspection points in green, and the final target point in yellow
    for index, (tx, ty) in enumerate(inspection_points):
        if index == len(inspection_points) - 1:
            # Final target point: yellow
            cv2.circle(path_image, (tx, ty), 7, (255, 255, 0), -1)
        else:
            # Inspection points: green
            cv2.circle(path_image, (tx, ty), 5, (0, 255, 0), -1)

    plt.figure(figsize=(12, 6))
    plt.imshow(path_image)
    plt.title("Planned Path on Largest Free-Space Component")
    plt.axis("off")

    output_path = os.path.join(output_dir, "planned_path.png")
    plt.savefig(output_path, dpi=300)

    plt.show()


if __name__ == "__main__":
    image_path = "pathGeneration/env.jpg"
    output_dir = "output_preprocessing"

    binary_map, occupancy_grid = preprocess_real_environment_image(
        image_path=image_path,
        output_dir=output_dir,
        resize_width=800,
        blur_kernel=5,
        threshold_value=120,
        use_canny=False,
        use_hsv_correction=True
    )

    # Keep only the largest connected free-space area
    occupancy_grid, largest_free_mask = keep_largest_free_component(occupancy_grid)

    # Update binary map for visualization
    binary_map = largest_free_mask

    # Save largest connected free-space map
    cv2.imwrite(
        os.path.join(output_dir, "largest_free_component.png"),
        largest_free_mask
    )

    # Automatically set start and target points from the same free-space component
    # Format: (x, y)
    start_point = find_top_left_free_point(occupancy_grid)
    target_point = find_bottom_right_free_point(occupancy_grid)

    print(f"Auto-selected start point: {start_point}")
    print(f"Auto-selected target point: {target_point}")

    # First, plan a direct feasible path from start to target
    direct_path = astar(occupancy_grid, start_point, target_point)

    if not direct_path:
        raise ValueError("No feasible path found from start point to target point.")

    # Select random inspection points from the feasible path
    inspection_points = select_random_inspection_points_from_path(
        direct_path,
        number_of_points=3
    )

    print(f"Random inspection points: {inspection_points}")

    # Re-plan final path through inspection points and target point
    final_path = plan_path_through_points(
        occupancy_grid,
        start_point,
        inspection_points + [target_point]
    )

    print(f"Final path length: {len(final_path)}")
    print("First 10 path points:")
    print(final_path[:10])

    # Save final path
    np.save(
        os.path.join(output_dir, "final_path.npy"),
        np.array(final_path)
    )

    np.savetxt(
        os.path.join(output_dir, "final_path.txt"),
        np.array(final_path),
        fmt="%d",
        delimiter=","
    )

    # Show path on binary map
    show_path_on_map(
        binary_map,
        final_path,
        start_point,
        inspection_points + [target_point],
        output_dir=output_dir
    )