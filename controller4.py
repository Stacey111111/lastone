#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Twist

from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory

from trajectory_msgs.msg import JointTrajectoryPoint

from builtin_interfaces.msg import Duration


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

        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory"
        )

        # Cooldown settings
        self.cooldown_time = 1.5
        self.last_command_time = 0

        self.last_command = ""

        self.get_logger().info(
            "Gesture Robot Controller Started"
        )

    # ------------------------------------------------
    # ARM CONTROL
    # ------------------------------------------------

    def send_arm_goal(self, positions, duration_sec=1.5):

        if not self.arm_client.wait_for_server(timeout_sec=2.0):

            self.get_logger().warn(
                "Arm action server not available"
            )

            return

        goal_msg = FollowJointTrajectory.Goal()

        goal_msg.trajectory.joint_names = [
            "joint1",
            "joint2",
            "joint3",
            "joint4"
        ]

        point = JointTrajectoryPoint()

        point.positions = positions

        point.time_from_start = Duration(
            sec=int(duration_sec),
            nanosec=int((duration_sec % 1.0) * 1e9)
        )

        goal_msg.trajectory.points.append(point)

        self.arm_client.send_goal_async(goal_msg)

    # ------------------------------------------------
    # WAVE MOTION
    # ------------------------------------------------

    def wave_arm(self):

        self.get_logger().info("Waving arm")

        wave_left = [0.8, -0.5, 0.3, 0.2]
        wave_right = [-0.8, -0.5, 0.3, 0.2]
        home = [0.0, 0.0, 0.0, 0.0]

        for _ in range(3):

            self.send_arm_goal(wave_left)
            time.sleep(1.5)

            self.send_arm_goal(wave_right)
            time.sleep(1.5)

        self.send_arm_goal(home)

    # ------------------------------------------------
    # ROBOT STOP
    # ------------------------------------------------

    def stop_robot(self):

        twist = Twist()

        self.cmd_pub.publish(twist)

    # ------------------------------------------------
    # GESTURE CALLBACK
    # ------------------------------------------------

    def command_callback(self, msg):

        command = msg.data.lower().strip()

        now = time.time()

        # Prevent rapid repeated commands
        if now - self.last_command_time < self.cooldown_time:
            return

        self.last_command_time = now

        twist = Twist()

        print("Received:", command)

        if command == "up":

            twist.linear.x = 0.15

        elif command == "down":

            twist.linear.x = -0.15

        elif command == "left":

            twist.angular.z = 0.7

        elif command == "right":

            twist.angular.z = -0.7

        elif command == "none":

            # self.stop_robot()

            self.wave_arm()

            return

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
