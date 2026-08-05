#!/usr/bin/env python3
"""
car_approach_node — map 좌표로 추적된 Car 지점으로 cmd_vel 로 직접 주행한다.

동작 (go-to-point)
  - /approach/enable(Bool) True 일 때만 동작. False 면 cmd_vel 0.
  - /robot/car_map_point(PointStamped, map) = 목표 지점(target_seeker 가 발행).
  - 매 제어주기: TF 로 로봇의 map 자세(map->base_frame)를 구하고,
    목표까지의 거리/방위오차를 계산해
      · 방위오차가 크면 제자리 회전(정렬)
      · 정렬되면 전진(거리에 비례), 미세 방위 보정 동시
    stop_distance 안에 들면 정지하고 arrived 발행. 히스테리시스로 재출발.
  - 안전: 목표점이 오래되면 정지, enable=False/종료 시 cmd_vel 0.

장애물(Dummy) 반응(선택, dummy_avoid)
  - /robot/detections 의 Dummy bbox 가 화면 중앙 근처에서 충분히 크면(가까움)
    전진을 줄이고 반대쪽으로 살짝 조향한다. depth 미사용 근사이므로 보조 수단이다.
  - 정식 장애물 회피는 Nav2 주행 구간(LiDAR costmap)에서 이뤄진다.
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from geometry_msgs.msg import PointStamped, Twist
from std_msgs.msg import Bool

import tf2_ros

from mini_pjt_interfaces.msg import DetectionArray, RobotState


def normalize_angle(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def yaw_from_quat(x, y, z, w):
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class CarApproach(Node):

    def __init__(self):
        super().__init__('car_approach_node')

        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')

        # 정지/재출발 (히스테리시스)
        self.declare_parameter('stop_distance', 0.35)     # 이 안이면 정지·도달
        self.declare_parameter('resume_distance', 0.45)   # 도달 후 이보다 멀어지면 재출발

        # 게인/제한
        self.declare_parameter('kp_lin', 0.6)
        self.declare_parameter('kp_ang', 1.2)
        self.declare_parameter('max_linear', 0.15)        # m/s
        self.declare_parameter('max_angular', 0.6)        # rad/s
        self.declare_parameter('min_linear', 0.04)        # 데드존 이하 전진은 이 값으로
        self.declare_parameter('min_angular', 0.10)
        self.declare_parameter('align_threshold', 0.30)   # rad, 이보다 크면 회전만

        self.declare_parameter('point_timeout_sec', 1.5)  # 목표점 신선도
        self.declare_parameter('control_rate_hz', 10.0)

        # Dummy 반응(보조)
        self.declare_parameter('dummy_avoid', True)
        self.declare_parameter('obstacle_class', 'Dummy')
        self.declare_parameter('image_width', 320)        # OAK-D preview 폭
        self.declare_parameter('dummy_center_band', 0.35)  # 화면폭 대비 중앙 밴드 비율
        self.declare_parameter('dummy_area_frac', 0.06)   # bbox 면적/화면면적 이 이상이면 '가까움'
        self.declare_parameter('dummy_steer', 0.4)        # rad/s 회피 조향
        self.declare_parameter('dummy_slow', 0.5)         # 전진 감속 배율

        # 토픽
        self.declare_parameter('cmd_vel_topic', '/robot8/cmd_vel')
        self.declare_parameter('enable_topic', '/approach/enable')
        self.declare_parameter('status_topic', '/approach/status')
        self.declare_parameter('car_map_point_topic', '/robot/car_map_point')
        self.declare_parameter('detections_topic', '/robot/detections')

        self.map_frame = str(self.get_parameter('map_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.stop_d = float(self.get_parameter('stop_distance').value)
        self.resume_d = float(self.get_parameter('resume_distance').value)
        self.kp_lin = float(self.get_parameter('kp_lin').value)
        self.kp_ang = float(self.get_parameter('kp_ang').value)
        self.max_lin = float(self.get_parameter('max_linear').value)
        self.max_ang = float(self.get_parameter('max_angular').value)
        self.min_lin = float(self.get_parameter('min_linear').value)
        self.min_ang = float(self.get_parameter('min_angular').value)
        self.align_th = float(self.get_parameter('align_threshold').value)
        self.point_timeout = float(self.get_parameter('point_timeout_sec').value)
        self.dummy_avoid = bool(self.get_parameter('dummy_avoid').value)
        self.obstacle_class = str(self.get_parameter('obstacle_class').value)
        self.image_width = int(self.get_parameter('image_width').value)
        self.dummy_band = float(self.get_parameter('dummy_center_band').value)
        self.dummy_area = float(self.get_parameter('dummy_area_frac').value)
        self.dummy_steer = float(self.get_parameter('dummy_steer').value)
        self.dummy_slow = float(self.get_parameter('dummy_slow').value)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.enabled = False
        self.arrived = False
        self.car_map = None       # (x, y)
        self.car_t = 0.0
        self.dummy_bias = 0.0     # 최근 dummy 회피 조향 성분

        self.cmd_pub = self.create_publisher(
            Twist, self.get_parameter('cmd_vel_topic').value, 10)
        self.status_pub = self.create_publisher(
            RobotState, self.get_parameter('status_topic').value, 10)

        self.create_subscription(
            Bool, self.get_parameter('enable_topic').value, self._enable_cb, 10)
        self.create_subscription(
            PointStamped, self.get_parameter('car_map_point_topic').value,
            self._point_cb, 10)
        if self.dummy_avoid:
            self.create_subscription(
                DetectionArray, self.get_parameter('detections_topic').value,
                self._det_cb, 10)

        rate = max(1.0, float(self.get_parameter('control_rate_hz').value))
        self.create_timer(1.0 / rate, self._control)

        self.get_logger().info(
            f'car_approach_node 시작 | stop={self.stop_d}m resume={self.resume_d}m '
            f'dummy_avoid={self.dummy_avoid}')

    # ------------------------------------------------------------------
    def _enable_cb(self, msg):
        en = bool(msg.data)
        if en != self.enabled:
            self.get_logger().info(f'approach enable = {en}')
        if not en:
            self.arrived = False
            self._stop()
        self.enabled = en

    def _point_cb(self, msg):
        self.car_map = (msg.point.x, msg.point.y)
        self.car_t = time.time()

    def _det_cb(self, msg):
        """Dummy 가 화면 중앙 근처에서 크면(가까움) 반대쪽 조향 바이어스."""
        bias = 0.0
        w = float(self.image_width)
        area_img = w * w  # preview 근사(정사각). 정확치 않아도 상대비교용.
        for d in msg.detections:
            if d.class_name != self.obstacle_class or len(d.bbox) < 4:
                continue
            x1, y1, x2, y2 = d.bbox[0], d.bbox[1], d.bbox[2], d.bbox[3]
            cx = (x1 + x2) / 2.0
            area = max(0, (x2 - x1)) * max(0, (y2 - y1))
            off = (cx - w / 2.0) / (w / 2.0)          # -1(좌)~+1(우)
            if abs(off) <= self.dummy_band and area >= self.dummy_area * area_img:
                # 중앙 근처 + 가까움 -> dummy 반대쪽으로 조향
                bias += -math.copysign(self.dummy_steer, off if off != 0 else 1.0)
        self.dummy_bias = clamp(bias, -self.max_ang, self.max_ang)

    # ------------------------------------------------------------------
    def _robot_pose(self):
        """map 프레임에서 (x, y, yaw). 실패 시 None."""
        try:
            tr = self.tf_buffer.lookup_transform(
                self.map_frame, self.base_frame, Time())
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f'로봇 자세 TF 실패: {e}', throttle_duration_sec=3.0)
            return None
        t = tr.transform.translation
        q = tr.transform.rotation
        return t.x, t.y, yaw_from_quat(q.x, q.y, q.z, q.w)

    def _stop(self):
        self.cmd_pub.publish(Twist())

    def _publish_status(self, state, dist):
        s = RobotState()
        s.header.stamp = self.get_clock().now().to_msg()
        s.header.frame_id = self.map_frame
        s.state = state
        s.target_distance = float(dist if dist is not None else -1.0)
        s.arrived = bool(self.arrived)
        self.status_pub.publish(s)

    # ------------------------------------------------------------------
    def _control(self):
        if not self.enabled:
            return

        now = time.time()
        if self.car_map is None or (now - self.car_t) > self.point_timeout:
            self._stop()
            self._publish_status('LOST', None)
            return

        pose = self._robot_pose()
        if pose is None:
            self._stop()
            self._publish_status('NO TF', None)
            return

        rx, ry, ryaw = pose
        dx, dy = self.car_map[0] - rx, self.car_map[1] - ry
        dist = math.hypot(dx, dy)
        heading_err = normalize_angle(math.atan2(dy, dx) - ryaw)

        # 히스테리시스 도달 판정
        if self.arrived:
            if dist >= self.resume_d:
                self.arrived = False
        elif dist <= self.stop_d:
            self.arrived = True

        if self.arrived:
            self._stop()
            self._publish_status('ARRIVED', dist)
            return

        cmd = Twist()
        if abs(heading_err) > self.align_th:
            # 정렬: 회전만
            w = clamp(self.kp_ang * heading_err, -self.max_ang, self.max_ang)
            if 0 < abs(w) < self.min_ang:
                w = math.copysign(self.min_ang, w)
            cmd.angular.z = w + self.dummy_bias
            self._publish_status('ALIGN', dist)
        else:
            # 접근: 전진 + 미세 조향 (+ dummy 회피 바이어스)
            v = clamp(self.kp_lin * (dist - self.stop_d), 0.0, self.max_lin)
            if 0 < v < self.min_lin:
                v = self.min_lin
            if self.dummy_bias != 0.0:
                v *= self.dummy_slow      # dummy 근접 시 감속
            w = clamp(self.kp_ang * heading_err, -self.max_ang, self.max_ang)
            cmd.linear.x = v
            cmd.angular.z = clamp(w + self.dummy_bias, -self.max_ang, self.max_ang)
            self._publish_status('APPROACH', dist)

        self.cmd_pub.publish(cmd)

    def destroy_node(self):
        try:
            self._stop()
        except Exception:                       # noqa: BLE001
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = CarApproach()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
