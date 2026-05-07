#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from std_msgs.msg import String

from geometry_msgs.msg import Twist


class GestureRobotController(Node):

    def __init__(self):

        super().__init__("gesture_robot_controller")

        self.subscription = self.create_subscription(
            String,
            "/gesture/command",
            self.command_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        self.get_logger().info(
            "Gesture Robot Controller Started"
        )

    def stop_robot(self):

        twist = Twist()

        self.cmd_pub.publish(twist)

    def command_callback(self, msg):

        command = msg.data.lower()

        twist = Twist()

        if command == "forward":

            twist.linear.x = 0.15

        elif command == "backward":

            twist.linear.x = -0.15

        elif command == "left":

            twist.angular.z = 0.7

        elif command == "right":

            twist.angular.z = -0.7

        elif command == "stop":

            twist.linear.x = 0.0
            twist.angular.z = 0.0

        else:

            twist.linear.x = 0.0
            twist.angular.z = 0.0

        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f"Robot Command: {command}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = GestureRobotController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()