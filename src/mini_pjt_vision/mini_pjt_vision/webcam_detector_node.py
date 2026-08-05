#!/usr/bin/env python3
"""
webcam_detector_node

web_my_data/webcam_detect.py 의 추론 로직을 그대로 유지한 채 ROS2 노드로 이식한 것.
외부 USB 웹캠(또는 mp4 파일)에서 프레임을 받아 YOLOv11n(best_v11n.pt)으로 rc_car('car')를
검출하고, N 프레임 연속 검출 시에만 트리거를 엣지 방식으로 발행한다.

실행 위치: 원격 PC (추론은 전부 여기서)

발행 토픽
  /webcam/annotated             sensor_msgs/Image            best_effort, depth 1  (base)
  /webcam/annotated/compressed  sensor_msgs/CompressedImage  best_effort, depth 1
        image_transport 규약대로 base(raw) 와 compressed 를 한 쌍으로 발행한다.
        annotated_transport 파라미터로 'both'|'raw'|'compressed' 선택 (기본 both).
  /webcam/detections  mini_pjt_interfaces/DetectionArray  reliable, depth 10
  /webcam/trigger     std_msgs/Bool                 reliable, TRANSIENT_LOCAL, depth 1

뷰어에서 보는 법 — 항상 base 토픽 '/webcam/annotated' 를 준다. '/compressed' 를 직접
주면 image_transport 가 타입 충돌로 죽는다.
  rqt_image_view : ros2 run rqt_image_view rqt_image_view /webcam/annotated
  rviz2          : Image 디스플레이, Topic '/webcam/annotated', Reliability 'Best Effort'.
                   Camera 디스플레이는 CameraInfo 가 필요한데 이 노드는 발행하지 않으므로
                   화면이 비어 보인다.

전처리 주의
  ultralytics 가 predict() 내부에서 letterbox(imgsz 정사각 패딩)를 수행하고,
  결과 bbox 는 원본 프레임 좌표계로 되돌려서 반환한다(results[0].orig_shape 기준).
  따라서 여기서 별도로 resize/letterbox 를 하면 이중 처리가 되어 좌표가 틀어진다.
  프레임은 손대지 않고 그대로 predict() 에 넘긴다.
"""

import os
import time

import cv2
import numpy as np

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

from std_msgs.msg import Bool
from sensor_msgs.msg import CompressedImage, Image

from mini_pjt_interfaces.msg import Detection, DetectionArray


class WebcamDetectorNode(Node):

    def __init__(self):
        super().__init__('webcam_detector_node')

        # ── 파라미터 ──────────────────────────────────────────
        self.declare_parameter('camera_index', 0)

        # camera_device 가 비어있지 않으면 camera_index 대신 이 경로를 쓴다.
        # USB 를 다시 꽂거나 커널이 장치를 재열거하면 /dev/videoN 의 N 이 바뀌므로
        # '/dev/v4l/by-id/usb-..._-video-index0' 처럼 이름 기반 심볼릭 링크를 쓰는 편이
        # 훨씬 안정적이다. 목록은 `ls -la /dev/v4l/by-id/` 로 확인한다.
        self.declare_parameter('camera_device', '')

        self.declare_parameter('video_path', '')        # 비우면 웹캠, 채우면 mp4 재생
        self.declare_parameter('loop_video', True)      # mp4 끝나면 처음으로

        # 프레임 취득이 계속 실패할 때 소스를 다시 여는 간격(초).
        # USB 가 재열거되는 중에는 몇 초 걸리므로 시간 기준으로 재시도한다.
        self.declare_parameter('reopen_interval_sec', 2.0)
        self.declare_parameter('model_path', '')
        self.declare_parameter('imgsz', 640)
        self.declare_parameter('conf_thres', 0.5)
        self.declare_parameter('target_class', 'car')
        self.declare_parameter('trigger_frames', 5)
        self.declare_parameter('publish_annotated', True)

        # annotated 스트림의 reliability: 'best_effort' | 'reliable'
        #   기본은 SensorDataQoS 관례대로 best_effort.
        #   rqt_image_view 는 BEST_EFFORT 로 구독하므로 이 기본값과 호환된다(실측 확인).
        #   RELIABLE 로 구독하는 도구를 쓸 때만 'reliable' 로 바꾸면 된다.
        self.declare_parameter('annotated_reliability', 'best_effort')

        self.declare_parameter('device', '0')           # GPU 번호 또는 'cpu'
        self.declare_parameter('target_fps', 30.0)
        self.declare_parameter('jpeg_quality', 80)
        self.declare_parameter('frame_id', 'webcam')
        # image_transport 규약: 하나의 이미지 스트림은 base 토픽(raw Image)과
        # '<base>/compressed'(CompressedImage) 를 한 쌍으로 광고한다.
        # rclpy 에는 image_transport 바인딩이 없어 두 퍼블리셔를 직접 만든다.
        # 압축본만 발행하면 뷰어들이 base 토픽을 찾지 못해 타입 충돌/구독 실패가 난다.
        self.declare_parameter('annotated_base_topic', '/webcam/annotated')

        # 'both' | 'raw' | 'compressed'
        #   both       - 기본. 어떤 뷰어에서도 그냥 열린다.
        #   raw        - 압축 비용 제거. 로컬 전용.
        #   compressed - 대역폭 절약. 단 base 토픽이 없어 뷰어 설정이 까다로워진다.
        self.declare_parameter('annotated_transport', 'both')
        self.declare_parameter('detections_topic', '/webcam/detections')
        self.declare_parameter('trigger_topic', '/webcam/trigger')

        self.video_path = self.get_parameter('video_path').value
        self.camera_index = self.get_parameter('camera_index').value
        self.camera_device = str(self.get_parameter('camera_device').value).strip()
        self.reopen_interval = float(self.get_parameter('reopen_interval_sec').value)
        self.loop_video = self.get_parameter('loop_video').value
        self.imgsz = self.get_parameter('imgsz').value
        self.conf_thres = float(self.get_parameter('conf_thres').value)
        self.target_class = self.get_parameter('target_class').value
        self.trigger_frames = int(self.get_parameter('trigger_frames').value)
        self.publish_annotated = self.get_parameter('publish_annotated').value
        self.jpeg_quality = int(self.get_parameter('jpeg_quality').value)
        self.frame_id = self.get_parameter('frame_id').value

        model_path = self.get_parameter('model_path').value
        if not model_path:
            raise RuntimeError('model_path 파라미터가 비어 있습니다. params.yaml 을 확인하세요.')

        # ultralytics 는 '0' 같은 문자열도 받지만, 정수로 넘기는 편이 안전하다.
        device = self.get_parameter('device').value
        self.device = int(device) if str(device).isdigit() else device

        # ── QoS ───────────────────────────────────────────────
        # annotated: 영상은 최신 프레임만 중요하므로 depth 1.
        # BEST_EFFORT 발행은 BEST_EFFORT 구독자와만 호환된다. rqt_image_view / rviz2 Image
        # 는 BEST_EFFORT 로 구독하므로 기본값 그대로 볼 수 있다.
        # RELIABLE 로만 구독하는 도구를 쓸 때는 파라미터를 'reliable' 로 바꾼다.
        rel = str(self.get_parameter('annotated_reliability').value).lower()
        qos_annotated = QoSProfile(depth=1)
        if rel == 'reliable':
            qos_annotated.reliability = ReliabilityPolicy.RELIABLE
        else:
            if rel != 'best_effort':
                self.get_logger().warn(
                    f"annotated_reliability='{rel}' 는 알 수 없는 값입니다. "
                    f"'best_effort' 로 처리합니다.")
            qos_annotated.reliability = ReliabilityPolicy.BEST_EFFORT

        # detections: 검출 결과는 유실되면 안 됨 -> reliable, depth 10
        qos_detections = QoSProfile(depth=10)
        qos_detections.reliability = ReliabilityPolicy.RELIABLE

        # trigger: 늦게 뜬 구독자(mission_manager)도 마지막 값을 받아야 함
        #          -> reliable + TRANSIENT_LOCAL, depth 1
        qos_trigger = QoSProfile(depth=1)
        qos_trigger.reliability = ReliabilityPolicy.RELIABLE
        qos_trigger.durability = DurabilityPolicy.TRANSIENT_LOCAL

        base_topic = str(self.get_parameter('annotated_base_topic').value).rstrip('/')
        transport = str(self.get_parameter('annotated_transport').value).lower()
        if transport not in ('both', 'raw', 'compressed'):
            self.get_logger().warn(
                f"annotated_transport='{transport}' 는 알 수 없는 값입니다. 'both' 로 처리합니다.")
            transport = 'both'

        self.raw_pub = None
        self.compressed_pub = None
        if transport in ('both', 'raw'):
            self.raw_pub = self.create_publisher(Image, base_topic, qos_annotated)
        if transport in ('both', 'compressed'):
            self.compressed_pub = self.create_publisher(
                CompressedImage, f'{base_topic}/compressed', qos_annotated)

        self.det_pub = self.create_publisher(
            DetectionArray, self.get_parameter('detections_topic').value, qos_detections)
        self.trigger_pub = self.create_publisher(
            Bool, self.get_parameter('trigger_topic').value, qos_trigger)

        # ── 모델 로드 ─────────────────────────────────────────
        from ultralytics import YOLO   # import 비용이 커서 여기서 로드
        self.model = YOLO(model_path)
        self.names = self.model.names
        self.get_logger().info(f'모델 로드 완료: {model_path}')
        self.get_logger().info(f'클래스: {self.names}')

        if self.target_class not in self.names.values():
            self.get_logger().error(
                f"target_class '{self.target_class}' 가 모델 클래스 {list(self.names.values())} "
                f"에 없습니다. 트리거가 절대 발생하지 않습니다.")

        # ── 입력 소스 ─────────────────────────────────────────
        self.cap = None
        self._open_capture()

        # ── 트리거 상태 (엣지 트리거) ─────────────────────────
        self.hit_count = 0
        self.triggered = False
        # 시작 시 False 를 1회 발행해 TRANSIENT_LOCAL 초기값을 남긴다.
        self.trigger_pub.publish(Bool(data=False))

        # ── 통계 ──────────────────────────────────────────────
        self.prev_time = time.time()
        self.fps = 0.0
        self.read_fail_count = 0
        self.infer_fail_count = 0
        self._last_reopen = 0.0

        target_fps = float(self.get_parameter('target_fps').value)
        self.timer = self.create_timer(1.0 / target_fps, self.timer_callback)

        self.get_logger().info(
            f'webcam_detector_node 시작 | conf>={self.conf_thres} '
            f'target={self.target_class} trigger_frames={self.trigger_frames}')

    # ------------------------------------------------------------------
    def _open_capture(self):
        """웹캠 또는 mp4 파일 열기. Linux 는 V4L2 백엔드를 쓴다(CAP_DSHOW 는 Windows 전용)."""
        if self.cap is not None:
            self.cap.release()

        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            src = f'video file: {self.video_path}'
        elif self.camera_device:
            # 심볼릭 링크는 재연결 때마다 실제 /dev/videoN 을 갈아끼우므로 매번 해석해 로그에 남긴다.
            real = os.path.realpath(self.camera_device)
            self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)
            src = f'device {self.camera_device} -> {real}'
        else:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            src = f'webcam index {self.camera_index}'

        if not self.cap.isOpened():
            raise RuntimeError(
                f'입력 소스를 열 수 없습니다 ({src}).\n'
                f'  - 장치 목록 확인: ls -la /dev/v4l/by-id/\n'
                f'  - USB 재연결 로그 확인: journalctl -k --since "5 min ago" | grep -i usb\n'
                f'  - 웹캠이면 camera_device 또는 camera_index 를, 파일이면 video_path 를 확인하세요.')

        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_logger().info(f'입력 소스 열림 — {src} ({w}x{h})')

    # ------------------------------------------------------------------
    def timer_callback(self):
        frame = self._read_frame()
        if frame is None:
            return

        result = self._infer(frame)
        if result is None:
            return

        detections = self._extract_detections(result)
        self._publish_detections(detections, frame.shape)
        self._update_trigger(detections)

        if self.publish_annotated:
            self._publish_annotated(result)

    # ------------------------------------------------------------------
    def _read_frame(self):
        """프레임 1장 취득. 실패해도 노드를 죽이지 않고 None 을 돌려준다."""
        try:
            ok, frame = self.cap.read()
        except Exception as e:                                  # noqa: BLE001
            self.get_logger().warn(f'cap.read() 예외: {e}', throttle_duration_sec=2.0)
            return None

        if not ok or frame is None:
            # mp4 재생이 끝난 경우 되감기
            if self.video_path and self.loop_video:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return None

            self.read_fail_count += 1
            self.get_logger().warn(
                f'프레임 취득 실패 (누적 {self.read_fail_count}회)',
                throttle_duration_sec=2.0)

            # 연속 실패가 길면 소스를 다시 연다 (USB 재열거 대응).
            # 재열거 중에는 몇 초간 장치가 없으므로 시간 기준으로 간격을 둔다.
            now = time.time()
            if now - self._last_reopen >= self.reopen_interval:
                self._last_reopen = now
                self.get_logger().warn('입력 소스 재오픈 시도', throttle_duration_sec=5.0)
                try:
                    self._open_capture()
                except Exception as e:                          # noqa: BLE001
                    self.get_logger().error(f'재오픈 실패: {e}', throttle_duration_sec=10.0)
            return None

        self.read_fail_count = 0
        return frame

    # ------------------------------------------------------------------
    def _infer(self, frame):
        """
        추론. 프레임을 리사이즈하지 않고 그대로 넘긴다.
        ultralytics 가 내부에서 letterbox 후 bbox 를 원본 좌표로 환산해 반환한다.
        """
        try:
            results = self.model.predict(
                frame,
                conf=self.conf_thres,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False,
            )
        except Exception as e:                                  # noqa: BLE001
            self.infer_fail_count += 1
            self.get_logger().warn(
                f'추론 실패 (누적 {self.infer_fail_count}회): {e}',
                throttle_duration_sec=2.0)
            return None

        now = time.time()
        dt = now - self.prev_time
        self.fps = (1.0 / dt) if dt > 0 else 0.0
        self.prev_time = now

        return results[0]

    # ------------------------------------------------------------------
    def _extract_detections(self, result):
        """result -> Detection 리스트. bbox 는 원본 프레임 픽셀 좌표."""
        out = []
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return out

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)

        oh, ow = result.orig_shape          # (height, width)

        for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clss):
            # 원본 프레임 범위로 clamp (letterbox 패딩 여파로 소수점 초과가 날 수 있음)
            x1 = int(np.clip(round(float(x1)), 0, ow - 1))
            y1 = int(np.clip(round(float(y1)), 0, oh - 1))
            x2 = int(np.clip(round(float(x2)), 0, ow - 1))
            y2 = int(np.clip(round(float(y2)), 0, oh - 1))

            det = Detection()
            det.class_name = str(self.names.get(int(cls_id), str(cls_id)))
            det.confidence = float(conf)
            det.center_x = (x1 + x2) // 2
            det.center_y = (y1 + y2) // 2
            det.bbox = [x1, y1, x2, y2]
            out.append(det)

        return out

    # ------------------------------------------------------------------
    def _publish_detections(self, detections, frame_shape):
        msg = DetectionArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.detections = detections
        self.det_pub.publish(msg)

    # ------------------------------------------------------------------
    def _update_trigger(self, detections):
        """
        엣지 트리거.
          - conf >= conf_thres 인 target_class 가 trigger_frames 연속 검출 -> True 1회
          - 검출이 끊기면 카운터 리셋 + (트리거 상태였다면) False 1회
        predict(conf=...) 로 이미 걸러지지만, 파라미터가 런타임에 바뀔 수 있으므로 한 번 더 확인한다.
        """
        hit = any(d.class_name == self.target_class and d.confidence >= self.conf_thres
                  for d in detections)

        if hit:
            self.hit_count += 1
            if self.hit_count >= self.trigger_frames and not self.triggered:
                self.triggered = True
                self.trigger_pub.publish(Bool(data=True))
                self.get_logger().info(
                    f'>>> TRIGGER=True ({self.target_class} {self.hit_count}프레임 연속 검출)')
        else:
            self.hit_count = 0
            if self.triggered:
                self.triggered = False
                self.trigger_pub.publish(Bool(data=False))
                self.get_logger().info('<<< TRIGGER=False (검출 끊김)')

    # ------------------------------------------------------------------
    def _publish_annotated(self, result):
        try:
            annotated = result.plot()      # 원본 webcam_detect.py 와 동일
            cv2.putText(annotated, f'FPS: {self.fps:.1f}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            stamp = self.get_clock().now().to_msg()

            # base 토픽: raw Image (bgr8)
            if self.raw_pub is not None:
                h, w = annotated.shape[:2]
                raw = Image()
                raw.header.stamp = stamp
                raw.header.frame_id = self.frame_id
                raw.height = h
                raw.width = w
                raw.encoding = 'bgr8'
                raw.is_bigendian = 0
                raw.step = w * 3
                raw.data = annotated.tobytes()
                self.raw_pub.publish(raw)

            # '<base>/compressed' 토픽: JPEG
            if self.compressed_pub is not None:
                ok, buf = cv2.imencode(
                    '.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
                if ok:
                    comp = CompressedImage()
                    comp.header.stamp = stamp
                    comp.header.frame_id = self.frame_id
                    comp.format = 'jpeg'
                    comp.data = buf.tobytes()
                    self.compressed_pub.publish(comp)
        except Exception as e:                                  # noqa: BLE001
            self.get_logger().warn(f'annotated 발행 실패: {e}', throttle_duration_sec=2.0)

    # ------------------------------------------------------------------
    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.get_logger().info('cap.release() 완료')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = WebcamDetectorNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:                       # noqa: BLE001
        # SIGTERM(예: launch 종료, timeout) 으로 컨텍스트가 먼저 내려가면
        # executor 가 RCLError 를 던진다. 정상 종료이므로 삼키고,
        # 컨텍스트가 살아있는 상태의 예외만 진짜 오류로 다시 던진다.
        if rclpy.ok():
            raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
