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

        # ------------------------------------------------
        # SUBSCRIBER
        # ------------------------------------------------
        self.subscription = self.create_subscription(
            String,
            "/gesture/command",
            self.command_callback,
            10
        )

        # ------------------------------------------------
        # PUBLISHER
        # ------------------------------------------------
        self.cmd_pub = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        # ------------------------------------------------
        # ARM ACTION CLIENT
        # ------------------------------------------------
        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory"
        )

        # ------------------------------------------------
        # GESTURE FILTERING VARIABLES
        # ------------------------------------------------
        self.last_gesture = None
        self.gesture_start_time = time.time()

        self.command_sent = False

        # Gesture must stay stable this long
        self.confirmation_time = 1.5

        # Delay between repeated commands
        self.cooldown_time = 2.0

        self.last_command_time = 0

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

        current_gesture = msg.data.lower().strip()

        # --------------------------------------------
        # Detect gesture change
        # --------------------------------------------
        if current_gesture != self.last_gesture:

            self.last_gesture = current_gesture
            self.gesture_start_time = time.time()

            self.command_sent = False

            return

        # --------------------------------------------
        # Calculate hold duration
        # --------------------------------------------
        elapsed = time.time() - self.gesture_start_time

        # --------------------------------------------
        # Cooldown protection
        # --------------------------------------------
        now = time.time()

        if now - self.last_command_time < self.cooldown_time:
            return

        # --------------------------------------------
        # Require stable gesture
        # --------------------------------------------
        if elapsed < self.confirmation_time:
            return

        # --------------------------------------------
        # Prevent repeated triggers
        # --------------------------------------------
        if self.command_sent:
            return

        twist = Twist()

        print("Confirmed Gesture:", current_gesture)

        # --------------------------------------------
        # MOVEMENT COMMANDS
        # --------------------------------------------
        if current_gesture == "up":

            twist.linear.x = 0.15

        elif current_gesture == "down":

            twist.linear.x = -0.15

        elif current_gesture == "left":

            twist.angular.z = 0.7

        elif current_gesture == "right":

            twist.angular.z = -0.7

        elif current_gesture == "stop":

            self.stop_robot()

            self.wave_arm()

            self.command_sent = True
            self.last_command_time = now

            return

        else:

            twist.linear.x = 0.0
            twist.angular.z = 0.0

        # --------------------------------------------
        # Publish movement
        # --------------------------------------------
        self.cmd_pub.publish(twist)

        self.command_sent = True
        self.last_command_time = now

        self.get_logger().info(
            f"Robot Command Executed: {current_gesture}"
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