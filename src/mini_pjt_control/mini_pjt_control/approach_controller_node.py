#!/usr/bin/env python3
"""
approach_controller_node — rc_car 근접 접근 제어

/approach/enable 이 True 일 때만 cmd_vel 을 낸다. False 면 정지 명령 후 대기.

제어식
  각속도  angular_z = -Kp_ang * (center_x - W/2) / (W/2)      # 정규화 오차 [-1, 1]
  선속도  linear_x  =  Kp_lin * (distance - stop_distance)

정렬 우선
  |정규화 x 오차| 가 align_threshold 를 넘으면 회전만 하고 전진하지 않는다.
  비스듬히 다가가다 목표를 놓치는 것을 막는다.

히스테리시스
  distance <= stop_distance(0.30) -> 정지, arrived=True
  arrived 상태에서 distance >= resume_distance(0.35) -> 접근 재개
  같은 임계값을 쓰면 경계에서 정지/전진을 반복한다.

안전장치
  - 검출이 detection_timeout_sec(1.0s) 이상 끊기면 즉시 정지
  - distance 가 NaN 이면 전진 금지 (거리를 모르는 상태)
  - enable=False 면 무조건 정지
  - 노드 종료/예외 시 반드시 cmd_vel 0 발행

cmd_vel 경합 주의
  TurtleBot4 에는 twist_mux 가 없어 Nav2 controller_server 도 같은 cmd_vel 로 쏜다.
  그래서 mission_manager_node 가 Nav2 를 cancelTask() 로 확실히 끊은 뒤에만
  /approach/enable 을 True 로 올린다.
"""

import math
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, Float32

from mini_pjt_interfaces.msg import DetectionArray, RobotState


class ApproachControllerNode(Node):

    def __init__(self):
        super().__init__('approach_controller_node')

        # ── 파라미터 ──────────────────────────────────────────
        self.declare_parameter('robot_namespace', '/robot8')

        # 정지 / 재개 (히스테리시스)
        self.declare_parameter('stop_distance', 0.30)
        self.declare_parameter('resume_distance', 0.35)

        # 게인
        self.declare_parameter('kp_lin', 0.5)
        self.declare_parameter('kp_ang', 0.8)

        # 속도 제한
        self.declare_parameter('max_linear', 0.15)      # m/s
        self.declare_parameter('max_angular', 0.5)      # rad/s
        # 데드존: 이 값보다 작은 명령은 바퀴가 안 도는데 전류만 먹으므로
        # 0 으로 만들거나 최소 구동 속도까지 올린다.
        self.declare_parameter('min_linear', 0.04)
        self.declare_parameter('min_angular', 0.12)

        # 정렬 우선: 정규화 오차(-1~1) 기준
        self.declare_parameter('align_threshold', 0.15)

        # 안전
        self.declare_parameter('detection_timeout_sec', 1.0)
        self.declare_parameter('control_rate_hz', 10.0)

        self.declare_parameter('image_width', 640)
        self.declare_parameter('target_class', 'car')

        self.declare_parameter('cmd_vel_topic', '/robot8/cmd_vel')
        self.declare_parameter('detections_topic', '/robot/detections')
        self.declare_parameter('distance_topic', '/robot/target_distance')
        self.declare_parameter('approach_enable_topic', '/approach/enable')
        # 도달 보고 토픽.
        # /robot/state 는 mission_manager_node 의 출력이라 발행자가 겹치지 않게 분리했다.
        # 굳이 합치려면 이 값을 '/robot/state' 로 바꾸면 되지만, 그러면 두 노드가
        # 같은 토픽에 쓰게 되어 상태 모니터링이 꼬인다.
        self.declare_parameter('state_topic', '/approach/status')

        self.stop_d = float(self.get_parameter('stop_distance').value)
        self.resume_d = float(self.get_parameter('resume_distance').value)
        self.kp_lin = float(self.get_parameter('kp_lin').value)
        self.kp_ang = float(self.get_parameter('kp_ang').value)
        self.max_lin = float(self.get_parameter('max_linear').value)
        self.max_ang = float(self.get_parameter('max_angular').value)
        self.min_lin = float(self.get_parameter('min_linear').value)
        self.min_ang = float(self.get_parameter('min_angular').value)
        self.align_th = float(self.get_parameter('align_threshold').value)
        self.det_timeout = float(self.get_parameter('detection_timeout_sec').value)
        self.image_width = int(self.get_parameter('image_width').value)
        self.target_class = str(self.get_parameter('target_class').value)

        if self.resume_d <= self.stop_d:
            self.get_logger().warn(
                f'resume_distance({self.resume_d}) 가 stop_distance({self.stop_d}) 이하입니다. '
                f'히스테리시스가 동작하지 않아 경계에서 떨립니다.')

        # ── 퍼블리셔 / 구독 ───────────────────────────────────
        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.RELIABLE

        self.cmd_pub = self.create_publisher(
            Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.state_pub = self.create_publisher(
            RobotState, self.get_parameter('state_topic').value, qos)

        self.create_subscription(
            Bool, self.get_parameter('approach_enable_topic').value,
            self._enable_cb, 10)
        self.create_subscription(
            DetectionArray, self.get_parameter('detections_topic').value,
            self._det_cb, qos)
        self.create_subscription(
            Float32, self.get_parameter('distance_topic').value,
            self._dist_cb, qos)

        # ── 상태 ──────────────────────────────────────────────
        self.enabled = False
        self.arrived = False
        self.center_x = None
        self.last_det_time = 0.0
        self.distance = float('nan')
        self.last_dist_time = 0.0
        self._last_state = ''

        period = 1.0 / float(self.get_parameter('control_rate_hz').value)
        self.create_timer(period, self._control_loop)

        self.get_logger().info(
            f'approach_controller_node 시작\n'
            f'  정지 {self.stop_d:.2f} m / 재개 {self.resume_d:.2f} m\n'
            f'  Kp_lin={self.kp_lin} Kp_ang={self.kp_ang}\n'
            f'  속도 상한 lin {self.max_lin} m/s, ang {self.max_ang} rad/s\n'
            f'  정렬 임계 {self.align_th}, 검출 타임아웃 {self.det_timeout} s\n'
            f'  cmd_vel -> {self.get_parameter("cmd_vel_topic").value}')

    # ==================================================================
    # 콜백
    # ==================================================================
    def _enable_cb(self, msg):
        new = bool(msg.data)
        if new != self.enabled:
            self.get_logger().info(f'/approach/enable = {new}')
            if not new:
                self._stop()
            else:
                # 재활성화 시 상태를 초기화한다.
                self.arrived = False
                self.center_x = None
                self.last_det_time = 0.0
        self.enabled = new

    def _det_cb(self, msg):
        for d in msg.detections:
            if d.class_name == self.target_class:
                self.center_x = int(d.center_x)
                self.last_det_time = time.time()
                if msg.header.frame_id and self.image_width <= 0:
                    pass
                return
        # target_class 가 없으면 갱신하지 않는다 -> 타임아웃으로 처리된다

    def _dist_cb(self, msg):
        self.distance = float(msg.data)
        self.last_dist_time = time.time()

    # ==================================================================
    # 유틸
    # ==================================================================
    @staticmethod
    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def _apply_deadzone(self, v, min_v, max_v):
        """
        데드존 처리: |v| 가 최소 구동 속도보다 작으면
          - 아주 작으면 0 (제어 종료 근처)
          - 그 사이면 최소 구동 속도까지 올린다
        """
        if abs(v) < 1e-4:
            return 0.0
        if abs(v) < min_v * 0.3:
            return 0.0
        if abs(v) < min_v:
            v = math.copysign(min_v, v)
        return self._clamp(v, -max_v, max_v)

    def _stop(self):
        self.cmd_pub.publish(Twist())

    def _publish_state(self, state):
        msg = RobotState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'approach'
        msg.state = state
        msg.target_distance = float(self.distance)
        msg.arrived = bool(self.arrived)
        self.state_pub.publish(msg)
        if state != self._last_state:
            self.get_logger().info(f'[접근] {self._last_state or "-"} -> {state}')
            self._last_state = state

    # ==================================================================
    # 제어 루프
    # ==================================================================
    def _control_loop(self):
        # --- 비활성: 무조건 정지 ---
        if not self.enabled:
            self._stop()
            self._publish_state('IDLE')
            return

        now = time.time()

        # --- 안전 1: 검출 소실 ---
        if self.center_x is None or (now - self.last_det_time) > self.det_timeout:
            self._stop()
            self._publish_state('LOST')
            self.get_logger().warn(
                f'검출 소실 {self.det_timeout:.1f}s 초과 — 정지', throttle_duration_sec=2.0)
            return

        # --- 안전 2: 거리 미상(NaN) 이면 전진 금지 ---
        dist_known = (self.distance is not None
                      and math.isfinite(self.distance)
                      and self.distance > 0.0
                      and (now - self.last_dist_time) <= self.det_timeout)

        # --- 정규화 x 오차 ---
        half = self.image_width / 2.0
        err_x = (self.center_x - half) / half           # -1(좌) ~ +1(우)

        # --- 히스테리시스 ---
        if dist_known:
            if not self.arrived and self.distance <= self.stop_d:
                self.arrived = True
                self.get_logger().info(
                    f'>>> 도달: {self.distance:.3f} m <= {self.stop_d:.2f} m')
            elif self.arrived and self.distance >= self.resume_d:
                self.arrived = False
                self.get_logger().info(
                    f'<<< 재개: {self.distance:.3f} m >= {self.resume_d:.2f} m')

        if self.arrived:
            self._stop()
            self._publish_state('ARRIVED')
            return

        # --- 각속도 ---
        ang = -self.kp_ang * err_x
        ang = self._apply_deadzone(ang, self.min_ang, self.max_ang)

        # --- 선속도 ---
        if not dist_known:
            # 거리를 모르면 회전만 허용 (전진 금지)
            lin = 0.0
            state = 'ALIGN(NO DEPTH)'
        elif abs(err_x) > self.align_th:
            # 정렬 우선: 아직 많이 틀어져 있으면 회전만
            lin = 0.0
            state = 'ALIGN'
        else:
            lin = self.kp_lin * (self.distance - self.stop_d)
            lin = max(0.0, lin)                          # 후진하지 않는다
            lin = self._apply_deadzone(lin, self.min_lin, self.max_lin)
            state = 'APPROACH'

        cmd = Twist()
        cmd.linear.x = float(lin)
        cmd.angular.z = float(ang)
        self.cmd_pub.publish(cmd)
        self._publish_state(state)

        self.get_logger().info(
            f'[{state}] err_x={err_x:+.3f} dist='
            + (f'{self.distance:.3f}m' if dist_known else 'NaN')
            + f' -> lin={lin:.3f} ang={ang:+.3f}',
            throttle_duration_sec=1.0)

    # ==================================================================
    def on_shutdown(self):
        """종료 시 반드시 정지 명령을 남긴다."""
        try:
            for _ in range(5):
                self._stop()
            self.get_logger().info('종료 — cmd_vel 0 발행 완료')
        except Exception:                               # noqa: BLE001
            pass

    def destroy_node(self):
        self.on_shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ApproachControllerNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:                                   # noqa: BLE001
        if rclpy.ok():
            raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
