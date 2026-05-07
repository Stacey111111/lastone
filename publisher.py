#!/usr/bin/env python3

import cv2
import rclpy

from rclpy.node import Node
from std_msgs.msg import String

from ultralytics import YOLO


class GestureVisionPublisher(Node):

    def __init__(self):

        super().__init__("gesture_vision_publisher")

        self.publisher_ = self.create_publisher(
            String,
            "/gesture/command",
            10
        )

        self.model = YOLO(
            "/root/best.pt"
        )

        self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.timer = self.create_timer(
            0.05,
            self.timer_callback
        )

        self.last_command = "none"

        self.get_logger().info(
            "Gesture Vision Publisher Started"
        )

    def timer_callback(self):

        ret, frame = self.cap.read()

        if not ret:
            return

        results = self.model(
            frame,
            verbose=False,
            imgsz=320
        )[0]

        best_conf = 0.0
        command = "none"

        for box in results.boxes:

            conf = float(box.conf[0])

            if conf < 0.30:
                continue

            class_id = int(box.cls[0])

            class_name = self.model.names[class_id]

            if conf > best_conf:

                best_conf = conf
                command = class_name

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                f"{class_name} {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,255,0),
                2
            )

        if command != self.last_command:

            msg = String()
            msg.data = command

            self.publisher_.publish(msg)

            self.get_logger().info(
                f"Published: {command}"
            )

            self.last_command = command

        cv2.imshow(
            "Gesture Detection",
            frame
        )

        key = cv2.waitKey(1)

        if key == 27:
            raise KeyboardInterrupt

    def destroy_node(self):

        self.cap.release()

        cv2.destroyAllWindows()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = GestureVisionPublisher()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
