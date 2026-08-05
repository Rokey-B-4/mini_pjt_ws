#!/usr/bin/env python3
"""
target_seeker_node — Car 의 픽셀(bbox) 위치를 map 좌표로 추적/표시한다.

파이프라인
  YOLO bbox 중심(픽셀) --(robot_detector: depth+K 역투영)--> /robot/target_point
     (카메라 광학프레임 3D)
  --(여기서 TF 로 map 투영)--> /robot/car_map_point (PointStamped, map)
                              + RViz 마커(/robot/car_marker) 로 "여기 있다" 표시
                              + /robot/seeking (Bool) 확인 여부

이 노드는 '어디에 있는지'만 map 좌표로 계산해 알린다. 실제 주행(cmd_vel)은
car_approach_node 가 이 map 좌표를 보고 수행한다.

인식은 OAK-D + 웹캠 둘 다 사용:
  - OAK-D : depth 로 실제 map 좌표 (car_map_point 의 근거)
  - 웹캠  : 넓은 시야에서 'Car 등장'을 조기 확인 (신뢰도 융합)
장애물(Dummy) 존재는 로그로 알린다.
"""

import time

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time

from geometry_msgs.msg import PointStamped
from std_msgs.msg import Bool
from visualization_msgs.msg import Marker

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  # PointStamped 의 do_transform 등록

from mini_pjt_interfaces.msg import DetectionArray


class TargetSeeker(Node):

    def __init__(self):
        super().__init__('target_seeker_node')

        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('target_class', 'Car')
        self.declare_parameter('obstacle_class', 'Dummy')

        self.declare_parameter('confirm_frames', 3)       # Car N회(양 카메라 합산) 확인
        self.declare_parameter('lost_timeout_sec', 2.0)   # Car 미검출 이 시간이면 확인 해제
        self.declare_parameter('point_timeout_sec', 1.0)  # OAK-D 3D 점 신선도
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('use_webcam', True)

        self.declare_parameter('target_point_topic', '/robot/target_point')
        self.declare_parameter('oakd_detections_topic', '/robot/detections')
        self.declare_parameter('webcam_detections_topic', '/webcam/detections')
        self.declare_parameter('car_map_point_topic', '/robot/car_map_point')
        self.declare_parameter('marker_topic', '/robot/car_marker')
        self.declare_parameter('seeking_topic', '/robot/seeking')

        self.map_frame = str(self.get_parameter('map_frame').value)
        self.target_class = str(self.get_parameter('target_class').value)
        self.obstacle_class = str(self.get_parameter('obstacle_class').value)
        self.confirm_frames = int(self.get_parameter('confirm_frames').value)
        self.lost_timeout = float(self.get_parameter('lost_timeout_sec').value)
        self.point_timeout = float(self.get_parameter('point_timeout_sec').value)
        self.use_webcam = bool(self.get_parameter('use_webcam').value)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.last_point = None        # 최신 Car PointStamped (카메라프레임)
        self.last_point_t = 0.0
        self.car_map = None           # 마지막으로 성공한 map 좌표 (x, y, z) — sticky
        self.car_hits = 0
        self.last_car_t = 0.0

        self.point_pub = self.create_publisher(
            PointStamped, self.get_parameter('car_map_point_topic').value, 10)
        self.marker_pub = self.create_publisher(
            Marker, self.get_parameter('marker_topic').value, 10)
        self.seeking_pub = self.create_publisher(
            Bool, self.get_parameter('seeking_topic').value, 10)

        self.create_subscription(
            PointStamped, self.get_parameter('target_point_topic').value,
            self._point_cb, 10)
        self.create_subscription(
            DetectionArray, self.get_parameter('oakd_detections_topic').value,
            lambda m: self._det_cb(m, 'OAK-D'), 10)
        if self.use_webcam:
            self.create_subscription(
                DetectionArray, self.get_parameter('webcam_detections_topic').value,
                lambda m: self._det_cb(m, 'webcam'), 10)

        self.create_timer(
            1.0 / max(1.0, float(self.get_parameter('publish_rate_hz').value)),
            self._tick)

        self.get_logger().info(
            f'target_seeker_node 시작 | target={self.target_class} '
            f'obstacle={self.obstacle_class} use_webcam={self.use_webcam}')

    # ------------------------------------------------------------------
    def _point_cb(self, msg):
        self.last_point = msg
        self.last_point_t = time.time()

    def _det_cb(self, msg, source):
        car = any(d.class_name == self.target_class for d in msg.detections)
        dummy = any(d.class_name == self.obstacle_class for d in msg.detections)
        if car:
            self.car_hits = min(self.car_hits + 1, self.confirm_frames * 3)
            self.last_car_t = time.time()
        if dummy:
            self.get_logger().info(
                f'[{source}] 장애물({self.obstacle_class}) 감지',
                throttle_duration_sec=3.0)

    # ------------------------------------------------------------------
    def _project_to_map(self):
        """최신 Car 3D 점을 map 으로 투영해 (x, y, z). 실패/오래되면 None."""
        if self.last_point is None:
            return None
        if time.time() - self.last_point_t > self.point_timeout:
            return None
        try:
            p = self.tf_buffer.transform(
                self.last_point, self.map_frame, timeout=Duration(seconds=0.2))
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException, tf2_ros.TransformException) as e:
            self.get_logger().warn(f'Car→map 투영 TF 실패: {e}', throttle_duration_sec=3.0)
            return None
        return (p.point.x, p.point.y, p.point.z)

    def _publish_marker(self, xyz, confirmed):
        m = Marker()
        m.header.frame_id = self.map_frame
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'car'
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position.x, m.pose.position.y, m.pose.position.z = xyz
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = m.scale.z = 0.3
        m.color.a = 0.9
        # 확인되면 초록, 미확인(과거값)이면 회색
        m.color.r, m.color.g, m.color.b = (0.0, 1.0, 0.0) if confirmed else (0.6, 0.6, 0.6)
        self.marker_pub.publish(m)

    # ------------------------------------------------------------------
    def _tick(self):
        now = time.time()
        if now - self.last_car_t > self.lost_timeout:
            self.car_hits = 0
        confirmed = self.car_hits >= self.confirm_frames
        self.seeking_pub.publish(Bool(data=bool(confirmed)))

        if confirmed:
            xyz = self._project_to_map()
            if xyz is not None:
                self.car_map = xyz      # sticky 갱신

        # 확인 상태에서 map 좌표가 있으면 발행 + 마커 (car 가 잠깐 사라져도 마지막 위치 유지)
        if confirmed and self.car_map is not None:
            pt = PointStamped()
            pt.header.stamp = self.get_clock().now().to_msg()
            pt.header.frame_id = self.map_frame
            pt.point.x, pt.point.y, pt.point.z = self.car_map
            self.point_pub.publish(pt)
            self._publish_marker(self.car_map, confirmed=True)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = TargetSeeker()
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
