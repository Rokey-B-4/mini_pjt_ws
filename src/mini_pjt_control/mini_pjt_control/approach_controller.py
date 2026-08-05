#!/usr/bin/env python3
"""
approach_controller (skeleton)

mission_manager 가 APPROACHING 상태로 진입시키면(approach_enable=True) 동작한다.
온보드 검출의 bbox 중심 x 오차로 yaw 를 정렬하고, depth 거리로 전진 속도를 제어하여
stop_distance_m(기본 0.3m) 이내에 도달하면 정지하고 arrived 를 발행한다.

안전 규칙 (Phase 3 구현 시):
  - approach_enable=False 이면 무조건 zero twist 발행 (또는 아무것도 발행하지 않음).
  - 검출이 detection_timeout_sec 이상 끊기면 즉시 정지.
  - linear/angular 속도는 파라미터 상한으로 clamp.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from std_msgs.msg import Bool, Float32
from geometry_msgs.msg import Twist

from mini_pjt_interfaces.msg import DetectionArray, RobotState


class ApproachController(Node):

    def __init__(self):
        super().__init__('approach_controller')

        # ── 파라미터 ──
        self.declare_parameter('robot_namespace', '/robot8')
        self.declare_parameter('stop_distance_m', 0.3)
        self.declare_parameter('distance_tolerance_m', 0.05)

        self.declare_parameter('max_linear_speed', 0.15)
        self.declare_parameter('max_angular_speed', 0.5)
        self.declare_parameter('kp_linear', 0.4)
        self.declare_parameter('kp_angular', 0.004)      # 픽셀 오차 -> rad/s
        self.declare_parameter('center_tolerance_px', 30)

        self.declare_parameter('image_width', 640)
        self.declare_parameter('target_class', 'car')
        self.declare_parameter('detection_timeout_sec', 1.0)
        self.declare_parameter('control_rate_hz', 10.0)

        self.declare_parameter('cmd_vel_topic', '/robot8/cmd_vel')
        self.declare_parameter('detections_topic', '/rc_car/onboard/detections')
        self.declare_parameter('distance_topic', '/rc_car/onboard/distance')
        self.declare_parameter('approach_enable_topic', '/approach/enable')
        self.declare_parameter('state_topic', '/approach/status')

        # ── 퍼블리셔 / 구독 ──
        self.cmd_pub = self.create_publisher(
            Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.state_pub = self.create_publisher(
            RobotState, self.get_parameter('state_topic').value, 10)

        self.create_subscription(
            Bool, self.get_parameter('approach_enable_topic').value,
            self.enable_callback, 10)
        self.create_subscription(
            DetectionArray, self.get_parameter('detections_topic').value,
            self.detections_callback, 10)
        self.create_subscription(
            Float32, self.get_parameter('distance_topic').value,
            self.distance_callback, 10)

        # ── 상태 ──
        self.enabled = False
        self.latest_detection = None
        self.latest_detection_time = None
        self.target_distance = -1.0
        self.arrived = False

        period = 1.0 / float(self.get_parameter('control_rate_hz').value)
        self.create_timer(period, self.control_loop)

        self.get_logger().info('approach_controller skeleton started')

    def enable_callback(self, msg):
        self.enabled = msg.data

    def detections_callback(self, msg):
        """target_class 검출만 골라 보관. Phase 3 에서 구현."""
        pass

    def distance_callback(self, msg):
        self.target_distance = msg.data

    def control_loop(self):
        """정렬 + 전진 제어. Phase 3 에서 구현."""
        pass

    def publish_stop(self):
        self.cmd_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = ApproachController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:                       # noqa: BLE001
        # SIGTERM 으로 컨텍스트가 먼저 내려가면 executor 가 RCLError 를 던진다.
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
