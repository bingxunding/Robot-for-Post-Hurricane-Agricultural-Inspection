import math

import rclpy
from rclpy.node import Node


class MotionController(Node):
    def __init__(self):
        super().__init__('motion_controller')

        self.waypoints = [
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
        ]

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.linear_speed = 0.1
        self.angular_speed = 0.15
        self.position_tolerance = 0.1
        self.angle_tolerance = 0.1

        self.current_waypoint_index = 0

        self.timer = self.create_timer(1.0, self.control_loop)

        self.get_logger().info('Motion controller started.')

    def normalize_angle(self, angle: float) -> float:
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def control_loop(self):
        if self.current_waypoint_index >= len(self.waypoints):
            self.get_logger().info('All waypoints reached.')
            return

        target_x, target_y = self.waypoints[self.current_waypoint_index]

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        target_angle = math.atan2(dy, dx)
        angle_error = self.normalize_angle(target_angle - self.yaw)

        if distance <= self.position_tolerance:
            self.get_logger().info(
                f'Waypoint {self.current_waypoint_index} reached at '
                f'({self.x:.2f}, {self.y:.2f}).'
            )
            self.current_waypoint_index += 1
            return

        if abs(angle_error) > self.angle_tolerance:
            turn_direction = 1.0 if angle_error > 0 else -1.0
            self.yaw += turn_direction * self.angular_speed
            self.yaw = self.normalize_angle(self.yaw)

            direction_text = 'left' if turn_direction > 0 else 'right'
            self.get_logger().info(
                f'Turning {direction_text} | '
                f'current yaw: {self.yaw:.2f} rad | '
                f'target angle: {target_angle:.2f} rad'
            )
            return

        step = min(self.linear_speed, distance)
        self.x += step * math.cos(self.yaw)
        self.y += step * math.sin(self.yaw)

        self.get_logger().info(
            f'Moving forward | '
            f'position: ({self.x:.2f}, {self.y:.2f}) | '
            f'target: ({target_x:.2f}, {target_y:.2f})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = MotionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
