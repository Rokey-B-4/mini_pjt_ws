#!/usr/bin/env python3
"""
robot_detector_node — TurtleBot4 온보드 검출 + 거리 산출

OAK-D 의 RGB 와 Depth 를 ApproximateTimeSynchronizer 로 동기화하고,
YOLOv8n 가중치로 rc_car('car')를 검출한 뒤 bbox 중심의 depth 로 거리를 낸다.
추론은 원격 PC 에서 수행한다 (로봇 토픽을 구독).

발행 토픽
  /robot/detections              mini_pjt_interfaces/DetectionArray
  /robot/target_distance         std_msgs/Float32          (없으면 -1.0)
  /robot/annotated               sensor_msgs/Image         (base, raw)
  /robot/annotated/compressed    sensor_msgs/CompressedImage

핵심 처리 세 가지
  1) QoS — 이미지 구독은 반드시 SensorDataQoS(best_effort).
     RELIABLE 로 구독하면 BEST_EFFORT 발행자와 QoS 비호환이라 한 프레임도 안 들어온다.

  2) RGB <-> Depth 좌표 정합
     OAK-D 의 RGB(preview)와 Depth(stereo)는 해상도도 FOV 도 다르다.
     RGB 픽셀 좌표를 그대로 depth 이미지에 쓰면 엉뚱한 곳의 거리를 읽는다.

     projection_mode='intrinsic' (기본, 정식)
        u_rgb -> RGB 정규화 좌표 : x = (u - cx_rgb) / fx_rgb
                                   y = (v - cy_rgb) / fy_rgb
        -> Depth 로 재투영        : u_d = fx_d * x + cx_d
                                   v_d = fy_d * y + cy_d
        두 카메라 사이 extrinsic(R,t)이 없으므로 '근사 동축'을 가정한다.
        베이스라인만큼의 시차는 남지만, 수 m 거리에서는 수 픽셀 수준이다.

     projection_mode='scale' (fallback)
        u_d = u_rgb * (W_depth / W_rgb),  v_d = v_rgb * (H_depth / H_rgb)
        FOV 가 같을 때만 맞다. 다르면 중심에서 멀수록 오차가 커진다.

     log_projection_compare=True 로 두면 두 방식의 결과를 함께 로그로 찍어 비교할 수 있다.

  3) depth encoding 런타임 판별
        16UC1 -> 밀리미터  -> / 1000.0
        32FC1 -> 미터      -> 그대로
     그 외 encoding 이면 에러 로그를 내고 그 프레임을 버린다.
"""

import time

import cv2
import numpy as np

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data

from std_msgs.msg import Float32
from sensor_msgs.msg import CameraInfo, CompressedImage, Image
from geometry_msgs.msg import PointStamped
from message_filters import ApproximateTimeSynchronizer, Subscriber

from mini_pjt_interfaces.msg import Detection, DetectionArray


class RobotDetectorNode(Node):

    def __init__(self):
        super().__init__('robot_detector_node')

        # ── 파라미터 ──────────────────────────────────────────
        self.declare_parameter('robot_namespace', '/robot8')
        # RGB 스트림 선택: 'preview'(교재 day2 기본, 이 로봇이 실제로 내보내는 스트림)
        #                  'isp'(풀 해상도, 있을 때만). oakd_probe 로 확인 후 선택.
        self.declare_parameter('rgb_stream', 'preview')
        self.declare_parameter('use_compressed_rgb', True)   # isp 모드에서만 의미 있음

        self.declare_parameter('model_path', '')
        self.declare_parameter('device', '0')
        self.declare_parameter('imgsz', 640)
        self.declare_parameter('conf_thres', 0.5)
        self.declare_parameter('target_class', 'car')

        # 동기화
        self.declare_parameter('sync_queue_size', 10)
        self.declare_parameter('sync_slop_sec', 0.05)
        self.declare_parameter('stats_period_sec', 5.0)

        # 좌표 정합
        self.declare_parameter('projection_mode', 'intrinsic')   # intrinsic | scale
        self.declare_parameter('log_projection_compare', True)

        # ── 거리 산출 ──
        # 중심 패치를 7x7 -> 11x11 -> 15x15 순으로 키우며 유효 픽셀을 모은다.
        self.declare_parameter('depth_patch_sizes', [7, 11, 15])
        self.declare_parameter('min_valid_pixels', 10)
        self.declare_parameter('min_valid_depth', 0.1)           # m
        self.declare_parameter('max_valid_depth', 10.0)          # m

        # 유효 픽셀이 계속 부족하면 직전 값을 hold 하다가, 임계를 넘으면 NaN 을 낸다.
        self.declare_parameter('hold_max_count', 10)

        # 저역통과 필터: filtered = alpha * raw + (1 - alpha) * prev
        #   alpha 1.0 = 필터 없음, 작을수록 부드럽지만 반응이 늦다.
        self.declare_parameter('lpf_alpha', 0.4)
        self.declare_parameter('log_distance_filter', True)

        # 출력
        self.declare_parameter('publish_annotated', True)
        self.declare_parameter('annotated_transport', 'both')    # both | raw | compressed
        self.declare_parameter('jpeg_quality', 80)
        self.declare_parameter('detections_topic', '/robot/detections')
        self.declare_parameter('distance_topic', '/robot/target_distance')
        self.declare_parameter('annotated_base_topic', '/robot/annotated')
        # Car 의 3D 위치(카메라 광학프레임)를 target_seeker 로 넘기는 토픽
        self.declare_parameter('target_point_topic', '/robot/target_point')

        self.ns = str(self.get_parameter('robot_namespace').value).rstrip('/')
        self.conf_thres = float(self.get_parameter('conf_thres').value)
        self.imgsz = int(self.get_parameter('imgsz').value)
        self.target_class = str(self.get_parameter('target_class').value)
        self.patch_sizes = [max(1, int(p))
                            for p in self.get_parameter('depth_patch_sizes').value]
        self.patch_sizes.sort()
        self.min_valid_px = int(self.get_parameter('min_valid_pixels').value)
        self.dmin = float(self.get_parameter('min_valid_depth').value)
        self.dmax = float(self.get_parameter('max_valid_depth').value)
        self.hold_max = int(self.get_parameter('hold_max_count').value)
        self.alpha = float(self.get_parameter('lpf_alpha').value)
        self.log_filter = bool(self.get_parameter('log_distance_filter').value)

        # 거리 필터 상태
        self.dist_filtered = None      # 직전 필터 출력 (m)
        self.hold_count = 0
        self.proj_mode = str(self.get_parameter('projection_mode').value).lower()
        self.log_compare = bool(self.get_parameter('log_projection_compare').value)
        self.publish_annotated = bool(self.get_parameter('publish_annotated').value)
        self.jpeg_quality = int(self.get_parameter('jpeg_quality').value)

        if self.proj_mode not in ('intrinsic', 'scale'):
            self.get_logger().warn(
                f"projection_mode='{self.proj_mode}' 는 알 수 없는 값입니다. 'intrinsic' 사용.")
            self.proj_mode = 'intrinsic'

        model_path = self.get_parameter('model_path').value
        if not model_path:
            raise RuntimeError('model_path 파라미터가 비어 있습니다.')
        device = self.get_parameter('device').value
        self.device = int(device) if str(device).isdigit() else device

        # ── 토픽 ──────────────────────────────────────────────
        rgb_stream = str(self.get_parameter('rgb_stream').value).lower()
        use_comp = bool(self.get_parameter('use_compressed_rgb').value)
        if rgb_stream == 'preview':
            # preview 는 압축본이 없는 경우가 많아 raw Image 로 받는다 (교재 day2 기준).
            self.rgb_topic = f'{self.ns}/oakd/rgb/preview/image_raw'
            self.rgb_type = Image
            self.rgb_info_topic = f'{self.ns}/oakd/rgb/preview/camera_info'
        else:  # isp / 풀 해상도
            self.rgb_topic = (f'{self.ns}/oakd/rgb/image_raw/compressed' if use_comp
                              else f'{self.ns}/oakd/rgb/image_raw')
            self.rgb_type = CompressedImage if use_comp else Image
            self.rgb_info_topic = f'{self.ns}/oakd/rgb/camera_info'
        self.depth_topic = f'{self.ns}/oakd/stereo/image_raw'
        self.depth_info_topic = f'{self.ns}/oakd/stereo/camera_info'

        # ── 퍼블리셔 ──────────────────────────────────────────
        qos_out = QoSProfile(depth=10)
        qos_out.reliability = ReliabilityPolicy.RELIABLE
        self.det_pub = self.create_publisher(
            DetectionArray, self.get_parameter('detections_topic').value, qos_out)
        self.dist_pub = self.create_publisher(
            Float32, self.get_parameter('distance_topic').value, qos_out)
        self.point_pub = self.create_publisher(
            PointStamped, self.get_parameter('target_point_topic').value, qos_out)

        base = str(self.get_parameter('annotated_base_topic').value).rstrip('/')
        transport = str(self.get_parameter('annotated_transport').value).lower()
        if transport not in ('both', 'raw', 'compressed'):
            transport = 'both'
        # image_transport 규약: base(raw) + '<base>/compressed' 를 쌍으로 발행한다.
        # 압축본만 내면 뷰어가 base 를 못 찾아 타입 충돌이 난다.
        self.raw_pub = (self.create_publisher(Image, base, qos_profile_sensor_data)
                        if transport in ('both', 'raw') else None)
        self.comp_pub = (self.create_publisher(
            CompressedImage, f'{base}/compressed', qos_profile_sensor_data)
            if transport in ('both', 'compressed') else None)

        # ── camera_info 구독 ──────────────────────────────────
        self.K_rgb = None
        self.K_depth = None
        self.rgb_info_size = None       # (w, h)
        self.depth_info_size = None
        self.create_subscription(
            CameraInfo, self.rgb_info_topic, self._rgb_info_cb, qos_profile_sensor_data)
        self.create_subscription(
            CameraInfo, self.depth_info_topic, self._depth_info_cb, qos_profile_sensor_data)

        # ── 동기화 구독 ───────────────────────────────────────
        # 이미지는 SensorDataQoS(best_effort) 여야 붙는다. RELIABLE 이면 한 장도 안 온다.
        self.rgb_sub = Subscriber(self, self.rgb_type, self.rgb_topic,
                                  qos_profile=qos_profile_sensor_data)
        self.depth_sub = Subscriber(self, Image, self.depth_topic,
                                    qos_profile=qos_profile_sensor_data)

        self.slop = float(self.get_parameter('sync_slop_sec').value)
        qsize = int(self.get_parameter('sync_queue_size').value)
        self.ts = ApproximateTimeSynchronizer(
            [self.rgb_sub, self.depth_sub], queue_size=qsize, slop=self.slop)
        self.ts.registerCallback(self._synced_cb)

        # 개별 수신 카운터 (드롭률 계산용)
        self.n_rgb = 0
        self.n_depth = 0
        self.n_sync = 0
        self.rgb_sub.registerCallback(self._count_rgb)
        self.depth_sub.registerCallback(self._count_depth)

        self._stat_t0 = time.time()
        self._stat_prev = (0, 0, 0)
        self.create_timer(
            float(self.get_parameter('stats_period_sec').value), self._log_stats)

        # ── 모델 ──────────────────────────────────────────────
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.names = self.model.names

        self._depth_enc_warned = set()
        self._logged_shapes = False

        self.get_logger().info(
            f'robot_detector_node 시작\n'
            f'  rgb        : {self.rgb_topic}\n'
            f'  depth      : {self.depth_topic}\n'
            f'  slop       : {self.slop:.3f} s   queue={qsize}\n'
            f'  projection : {self.proj_mode}\n'
            f'  model      : {model_path}\n'
            f'  classes    : {self.names}')

    # ==================================================================
    # camera_info
    # ==================================================================
    def _rgb_info_cb(self, msg):
        if self.K_rgb is None:
            self.get_logger().info(
                f'RGB camera_info: {msg.width}x{msg.height} '
                f'fx={msg.k[0]:.2f} fy={msg.k[4]:.2f} cx={msg.k[2]:.2f} cy={msg.k[5]:.2f}')
        self.K_rgb = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.rgb_info_size = (msg.width, msg.height)

    def _depth_info_cb(self, msg):
        if self.K_depth is None:
            self.get_logger().info(
                f'Depth camera_info: {msg.width}x{msg.height} '
                f'fx={msg.k[0]:.2f} fy={msg.k[4]:.2f} cx={msg.k[2]:.2f} cy={msg.k[5]:.2f}')
        self.K_depth = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.depth_info_size = (msg.width, msg.height)

    # ==================================================================
    # 통계
    # ==================================================================
    def _count_rgb(self, _):
        self.n_rgb += 1

    def _count_depth(self, _):
        self.n_depth += 1

    def _log_stats(self):
        now = time.time()
        dt = now - self._stat_t0
        self._stat_t0 = now
        pr, pd, ps = self._stat_prev
        d_rgb, d_dep, d_sync = self.n_rgb - pr, self.n_depth - pd, self.n_sync - ps
        self._stat_prev = (self.n_rgb, self.n_depth, self.n_sync)

        if dt <= 0:
            return
        pairable = min(d_rgb, d_dep)
        drop = (1.0 - d_sync / pairable) * 100.0 if pairable > 0 else 0.0

        self.get_logger().info(
            f'[동기화] rgb {d_rgb/dt:5.1f} Hz | depth {d_dep/dt:5.1f} Hz | '
            f'sync {d_sync/dt:5.1f} Hz | 드롭 {drop:5.1f}% (slop={self.slop:.3f}s)')

        if pairable > 0 and drop > 50.0:
            self.get_logger().warn(
                f'동기화 드롭률이 {drop:.0f}% 입니다. slop 을 키우거나 '
                f'(현재 {self.slop:.3f}s) 카메라 fps 를 확인하세요.')
        if d_rgb == 0 or d_dep == 0:
            missing = 'RGB' if d_rgb == 0 else 'Depth'
            self.get_logger().warn(
                f'{missing} 토픽 수신 없음. lazy publisher 또는 QoS 를 확인하세요:\n'
                f'  ros2 param set {self.ns}/oakd rgb.i_enable_lazy_publisher false\n'
                f'  ros2 param set {self.ns}/oakd stereo.i_enable_lazy_publisher false')

    # ==================================================================
    # depth 변환
    # ==================================================================
    def _depth_to_meters(self, depth_msg):
        """
        encoding 을 런타임에 판별해 미터 단위 float 배열로 바꾼다.
          16UC1 -> mm  -> /1000
          32FC1 -> m   -> 그대로
        예상 밖이면 None 을 돌려주고 에러 로그를 남긴다.
        """
        enc = depth_msg.encoding
        h, w = depth_msg.height, depth_msg.width

        if enc in ('16UC1', 'mono16'):
            arr = np.frombuffer(depth_msg.data, dtype=np.uint16).reshape(h, w)
            return arr.astype(np.float32) / 1000.0
        if enc == '32FC1':
            arr = np.frombuffer(depth_msg.data, dtype=np.float32).reshape(h, w)
            return arr.astype(np.float32)

        if enc not in self._depth_enc_warned:
            self._depth_enc_warned.add(enc)
            self.get_logger().error(
                f"예상 밖의 depth encoding '{enc}' 입니다. "
                f"지원: 16UC1(mm), mono16(mm), 32FC1(m). 이 프레임은 버립니다.")
        return None

    # ==================================================================
    # 좌표 정합
    # ==================================================================
    def _rgb_to_depth_px(self, u, v, rgb_shape, depth_shape):
        """
        RGB 픽셀 (u, v) -> Depth 픽셀 (u_d, v_d).

        :return: (u_d, v_d, 사용한 방식, 비교용 다른방식 결과 or None)
        """
        hr, wr = rgb_shape[:2]
        hd, wd = depth_shape[:2]

        # --- 단순 스케일 ---
        sx, sy = wd / float(wr), hd / float(hr)
        scale_uv = (u * sx, v * sy)

        # --- K 행렬 기반 ---
        intr_uv = None
        if self.K_rgb is not None and self.K_depth is not None:
            kr, kd = self.K_rgb, self.K_depth

            # camera_info 는 원본 센서 해상도 기준이다.
            # 실제로 받은 이미지가 그와 다르면(리사이즈된 preview 등) K 를 맞춰 보정한다.
            krx = kry = 1.0
            if self.rgb_info_size and self.rgb_info_size[0] > 0:
                krx = wr / float(self.rgb_info_size[0])
                kry = hr / float(self.rgb_info_size[1])
            kdx = kdy = 1.0
            if self.depth_info_size and self.depth_info_size[0] > 0:
                kdx = wd / float(self.depth_info_size[0])
                kdy = hd / float(self.depth_info_size[1])

            fx_r, fy_r = kr[0, 0] * krx, kr[1, 1] * kry
            cx_r, cy_r = kr[0, 2] * krx, kr[1, 2] * kry
            fx_d, fy_d = kd[0, 0] * kdx, kd[1, 1] * kdy
            cx_d, cy_d = kd[0, 2] * kdx, kd[1, 2] * kdy

            if fx_r > 0 and fy_r > 0:
                # 1) RGB 픽셀 -> 정규화 좌표
                xn = (u - cx_r) / fx_r
                yn = (v - cy_r) / fy_r
                # 2) 근사 동축 가정 하에 Depth 로 재투영
                intr_uv = (fx_d * xn + cx_d, fy_d * yn + cy_d)

        if self.proj_mode == 'intrinsic' and intr_uv is not None:
            return intr_uv[0], intr_uv[1], 'intrinsic', scale_uv
        if self.proj_mode == 'intrinsic' and intr_uv is None:
            # camera_info 가 아직 안 왔으면 스케일로 버틴다
            return scale_uv[0], scale_uv[1], 'scale(fallback)', None
        return scale_uv[0], scale_uv[1], 'scale', intr_uv

    def _scaled_depth_K(self, depth_shape):
        """실제 depth 이미지 해상도에 맞춘 (fx, fy, cx, cy). camera_info 없으면 None."""
        if self.K_depth is None:
            return None
        hd, wd = depth_shape[:2]
        kdx = kdy = 1.0
        if self.depth_info_size and self.depth_info_size[0] > 0:
            kdx = wd / float(self.depth_info_size[0])
            kdy = hd / float(self.depth_info_size[1])
        kd = self.K_depth
        return (kd[0, 0] * kdx, kd[1, 1] * kdy, kd[0, 2] * kdx, kd[1, 2] * kdy)

    def _backproject(self, u_d, v_d, z, depth_shape):
        """
        depth 픽셀 (u_d, v_d) + 거리 z(m) -> 카메라 광학프레임 3D 점 (x,y,z) m.
        광학프레임 규약: x 오른쪽, y 아래, z 정면(광축).
        """
        K = self._scaled_depth_K(depth_shape)
        if K is None or z is None or z <= 0:
            return None
        fx, fy, cx, cy = K
        if fx <= 0 or fy <= 0:
            return None
        x = (u_d - cx) / fx * z
        y = (v_d - cy) / fy * z
        return (float(x), float(y), float(z))

    # ==================================================================
    # 거리 산출
    # ==================================================================
    def _patch_valid_values(self, depth_m, u_d, v_d, size):
        """
        중심 (u_d, v_d) 의 size x size 패치에서 유효 depth 값만 뽑는다.

        제외 대상: 0, NaN, inf, [min_valid_depth, max_valid_depth] 범위 밖.
        패치가 이미지 밖으로 나가면 경계에 맞춰 잘라낸다(클리핑).
        """
        h, w = depth_m.shape[:2]
        ui, vi = int(round(u_d)), int(round(v_d))
        if not (0 <= ui < w and 0 <= vi < h):
            return np.empty(0, dtype=np.float32)

        r = size // 2
        u0, u1 = max(0, ui - r), min(w, ui + r + 1)
        v0, v1 = max(0, vi - r), min(h, vi + r + 1)
        patch = depth_m[v0:v1, u0:u1].reshape(-1)

        # np.isfinite 가 NaN 과 inf 를 동시에 걸러낸다. 0 은 하한으로 제외된다.
        return patch[np.isfinite(patch) & (patch >= self.dmin) & (patch <= self.dmax)]

    # ------------------------------------------------------------------
    def _patch_distance(self, depth_m, u_d, v_d):
        """
        패치를 7 -> 11 -> 15 순으로 키우며 유효 픽셀이 min_valid_pixels 이상 모이면
        그 median 을 돌려준다.

        :return: (거리 or None, 유효픽셀수, 사용한 패치크기)
        """
        last_n, last_size = 0, self.patch_sizes[-1] if self.patch_sizes else 7
        for size in self.patch_sizes:
            vals = self._patch_valid_values(depth_m, u_d, v_d, size)
            last_n, last_size = vals.size, size
            if vals.size >= self.min_valid_px:
                return float(np.median(vals)), int(vals.size), size
        return None, int(last_n), last_size

    # ------------------------------------------------------------------
    def _update_distance_filter(self, raw, n_valid, patch_size):
        """
        hold 로직 + 저역통과 필터.

        유효 픽셀이 부족하면(raw is None) 직전 값을 유지하며 hold_count 를 올리고,
        hold_max_count 를 넘으면 NaN 을 발행해 '거리 모름'을 명확히 알린다.
        접근 제어 노드는 NaN 이면 전진하지 않는다.

        :return: 발행할 거리값 (m, 또는 float('nan'))
        """
        if raw is None:
            self.hold_count += 1
            if self.hold_count > self.hold_max or self.dist_filtered is None:
                if self.log_filter:
                    self.get_logger().warn(
                        f'[거리] 유효픽셀 {n_valid}개(<{self.min_valid_px}), '
                        f'hold {self.hold_count}회 초과 -> NaN 발행',
                        throttle_duration_sec=2.0)
                self.dist_filtered = None
                return float('nan')

            if self.log_filter:
                self.get_logger().warn(
                    f'[거리] 유효픽셀 {n_valid}개(<{self.min_valid_px}), '
                    f'직전값 {self.dist_filtered:.3f} m 유지 (hold {self.hold_count}/{self.hold_max})',
                    throttle_duration_sec=2.0)
            return self.dist_filtered

        self.hold_count = 0
        prev = self.dist_filtered
        if prev is None:
            filtered = raw
        else:
            filtered = self.alpha * raw + (1.0 - self.alpha) * prev
        self.dist_filtered = filtered

        if self.log_filter:
            self.get_logger().info(
                f'[거리] raw {raw:.3f} m -> filtered {filtered:.3f} m '
                f'(alpha={self.alpha}, 유효 {n_valid}px, 패치 {patch_size}x{patch_size})',
                throttle_duration_sec=1.0)
        return filtered

    # ==================================================================
    # 동기화 콜백
    # ==================================================================
    def _synced_cb(self, rgb_msg, depth_msg):
        self.n_sync += 1

        # --- RGB 디코드 ---
        try:
            if isinstance(rgb_msg, CompressedImage):
                rgb = cv2.imdecode(np.frombuffer(rgb_msg.data, np.uint8), cv2.IMREAD_COLOR)
            else:
                rgb = np.frombuffer(rgb_msg.data, dtype=np.uint8).reshape(
                    rgb_msg.height, rgb_msg.width, -1)
                if rgb_msg.encoding in ('rgb8',):
                    rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        except Exception as e:                                  # noqa: BLE001
            self.get_logger().warn(f'RGB 디코드 실패: {e}', throttle_duration_sec=2.0)
            return
        if rgb is None or rgb.size == 0:
            return

        # --- Depth 변환 ---
        depth_m = self._depth_to_meters(depth_msg)
        if depth_m is None:
            return

        if not self._logged_shapes:
            self._logged_shapes = True
            self.get_logger().info(
                f'첫 동기화 프레임 — RGB {rgb.shape[1]}x{rgb.shape[0]}, '
                f'Depth {depth_m.shape[1]}x{depth_m.shape[0]} ({depth_msg.encoding})')

        # --- 추론 (프레임을 리사이즈하지 않는다. ultralytics 가 내부 letterbox 후
        #     원본 좌표로 되돌려 반환한다) ---
        try:
            result = self.model.predict(rgb, conf=self.conf_thres, imgsz=self.imgsz,
                                        device=self.device, verbose=False)[0]
        except Exception as e:                                  # noqa: BLE001
            self.get_logger().warn(f'추론 실패: {e}', throttle_duration_sec=2.0)
            return

        detections, raw, n_valid, patch_size, best_point = self._build_detections(
            result, rgb.shape, depth_m)

        cam_frame = depth_msg.header.frame_id or 'oakd_rgb_camera_optical_frame'

        msg = DetectionArray()
        msg.header.stamp = rgb_msg.header.stamp     # 원본 프레임 시각을 유지
        msg.header.frame_id = cam_frame
        msg.detections = detections
        self.det_pub.publish(msg)

        # Car 3D 위치 발행 (target_seeker 가 map 으로 투영해 Nav2 목표로 씀)
        if best_point is not None:
            pt = PointStamped()
            pt.header.stamp = rgb_msg.header.stamp
            pt.header.frame_id = cam_frame
            pt.point.x, pt.point.y, pt.point.z = best_point
            self.point_pub.publish(pt)

        # 대상이 아예 안 잡힌 경우와, 잡혔는데 depth 를 못 읽은 경우를 구분한다.
        #   대상 없음      -> -1.0
        #   대상 있음/거리? -> hold 또는 NaN
        if raw is None and n_valid < 0:
            distance = -1.0
            self.hold_count = 0
            self.dist_filtered = None
        else:
            distance = self._update_distance_filter(raw, n_valid, patch_size)

        self.dist_pub.publish(Float32(data=float(distance)))

        if self.publish_annotated:
            self._publish_annotated(result, detections, distance, rgb_msg.header.stamp,
                                    msg.header.frame_id)

    # ------------------------------------------------------------------
    def _build_detections(self, result, rgb_shape, depth_m):
        """
        검출 -> Detection 리스트.

        :return: (detections, best_raw, n_valid, patch_size, best_point)
                 best_point 은 가장 가까운 target 의 카메라프레임 3D 점(없으면 None).
                 대상 클래스가 하나도 없으면 n_valid = -1 로 표시한다.
        """
        out = []
        best = None
        best_ud = best_vd = None
        best_n, best_patch = -1, self.patch_sizes[0] if self.patch_sizes else 7
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return out, None, -1, best_patch, None

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        oh, ow = result.orig_shape

        for (x1, y1, x2, y2), conf, cid in zip(xyxy, confs, clss):
            x1 = int(np.clip(round(float(x1)), 0, ow - 1))
            y1 = int(np.clip(round(float(y1)), 0, oh - 1))
            x2 = int(np.clip(round(float(x2)), 0, ow - 1))
            y2 = int(np.clip(round(float(y2)), 0, oh - 1))
            cu, cv_ = (x1 + x2) // 2, (y1 + y2) // 2

            det = Detection()
            det.class_name = str(self.names.get(int(cid), str(cid)))
            det.confidence = float(conf)
            det.center_x = cu
            det.center_y = cv_
            det.bbox = [x1, y1, x2, y2]
            out.append(det)

            if det.class_name != self.target_class:
                continue

            u_d, v_d, used, other = self._rgb_to_depth_px(
                cu, cv_, rgb_shape, depth_m.shape)
            dist, n_valid, used_patch = self._patch_distance(depth_m, u_d, v_d)
            if best_n < 0:
                best_n, best_patch = n_valid, used_patch

            if self.log_compare and other is not None:
                d_other, _, _ = self._patch_distance(depth_m, other[0], other[1])
                du = abs(u_d - other[0])
                dv = abs(v_d - other[1])
                self.get_logger().info(
                    f'[정합비교] rgb({cu},{cv_}) -> {used} ({u_d:.1f},{v_d:.1f}) '
                    f'd={dist if dist is None else round(dist, 3)} m | '
                    f'other ({other[0]:.1f},{other[1]:.1f}) '
                    f'd={d_other if d_other is None else round(d_other, 3)} m | '
                    f'픽셀차 ({du:.1f},{dv:.1f})',
                    throttle_duration_sec=2.0)

            if dist is not None and (best is None or dist < best):
                best = dist
                best_n, best_patch = n_valid, used_patch
                best_ud, best_vd = u_d, v_d

        best_point = None
        if best is not None and best_ud is not None:
            best_point = self._backproject(best_ud, best_vd, best, depth_m.shape)
        return out, best, best_n, best_patch, best_point

    # ------------------------------------------------------------------
    def _publish_annotated(self, result, detections, distance, stamp, frame_id):
        try:
            img = result.plot()
            if distance is None or distance < 0:
                label, color = 'no target', (0, 0, 255)
            elif not np.isfinite(distance):
                label, color = 'distance UNKNOWN', (0, 0, 255)
            else:
                label, color = f'{distance:.2f} m', (0, 255, 0)
            cv2.putText(img, label, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

            if self.raw_pub is not None:
                h, w = img.shape[:2]
                raw = Image()
                raw.header.stamp = stamp
                raw.header.frame_id = frame_id
                raw.height, raw.width = h, w
                raw.encoding = 'bgr8'
                raw.is_bigendian = 0
                raw.step = w * 3
                raw.data = img.tobytes()
                self.raw_pub.publish(raw)

            if self.comp_pub is not None:
                ok, buf = cv2.imencode(
                    '.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
                if ok:
                    c = CompressedImage()
                    c.header.stamp = stamp
                    c.header.frame_id = frame_id
                    c.format = 'jpeg'
                    c.data = buf.tobytes()
                    self.comp_pub.publish(c)
        except Exception as e:                                  # noqa: BLE001
            self.get_logger().warn(f'annotated 발행 실패: {e}', throttle_duration_sec=2.0)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = RobotDetectorNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:                                           # noqa: BLE001
        if rclpy.ok():
            raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
