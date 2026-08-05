#!/usr/bin/env python3
"""
oakd_probe — TurtleBot4 OAK-D 진단 스크립트

출력 내용
  1) /<ns>/oakd/ 하위 모든 토픽: 이름, 타입, 해상도, encoding, frame_id, 발행 주기
  2) rgb / depth 의 camera_info: K 행렬, D, 해상도, distortion_model 을 나란히 비교
  3) rgb 와 depth 의 header.stamp 차이 분포 (평균/최대/표준편차) — 기본 100 샘플

사용법
  ros2 run mini_pjt_vision oakd_probe
  ros2 run mini_pjt_vision oakd_probe --ns /robot8 --samples 100 --timeout 60

lazy publisher 주의
  depthai_ros_driver 는 구독자가 붙기 전에는 카메라 스트림을 시작하지 않는다
  (rgb.i_enable_lazy_publisher / stereo.i_enable_lazy_publisher).
  그래서 `ros2 topic list` 에 안 보이는 경우가 있는데, 이 스크립트는
  '알려진 토픽 이름으로 무조건 구독(blind subscribe)' 도 함께 시도하므로
  그 상태에서도 측정할 수 있다.

  그래도 안 나오면 lazy 를 꺼본다:
    ros2 param set /robot8/oakd rgb.i_enable_lazy_publisher false
    ros2 param set /robot8/oakd stereo.i_enable_lazy_publisher false
"""

import argparse
import statistics
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import CameraInfo, CompressedImage, Image

# 무조건 구독을 시도할 후보 토픽 (lazy publisher 대응).
# suffix -> (메시지 타입, 역할)
CANDIDATES = [
    # 교재 day2 기준, 이 로봇의 RGB 는 preview 스트림으로 나온다.
    ('rgb/preview/image_raw', Image, 'RGB preview raw'),
    ('rgb/preview/image_raw/compressed', CompressedImage, 'RGB preview compressed'),
    ('rgb/preview/camera_info', CameraInfo, 'RGB preview camera_info'),
    # ISP(풀 해상도) 스트림 — 설정에 따라 있을 수도, 없을 수도 있다.
    ('rgb/image_raw', Image, 'RGB isp raw'),
    ('rgb/image_raw/compressed', CompressedImage, 'RGB isp compressed'),
    ('rgb/camera_info', CameraInfo, 'RGB isp camera_info'),
    ('stereo/image_raw', Image, 'Depth raw'),
    ('stereo/image_raw/compressed', CompressedImage, 'Depth compressed'),
    ('stereo/camera_info', CameraInfo, 'Depth camera_info'),
    ('left/image_raw', Image, 'Left mono'),
    ('right/image_raw', Image, 'Right mono'),
]

TYPE_MAP = {
    'sensor_msgs/msg/Image': Image,
    'sensor_msgs/msg/CompressedImage': CompressedImage,
    'sensor_msgs/msg/CameraInfo': CameraInfo,
}


class TopicStat:
    """토픽 하나의 수신 통계."""

    def __init__(self, topic, type_name, role=''):
        self.topic = topic
        self.type_name = type_name
        self.role = role
        self.count = 0
        self.first_wall = None
        self.last_wall = None
        self.stamps = []          # header.stamp (초, float)
        self.info = {}            # 해상도/encoding/frame_id 등

    def on_msg(self, msg):
        now = time.time()
        if self.first_wall is None:
            self.first_wall = now
        self.last_wall = now
        self.count += 1

        st = msg.header.stamp
        self.stamps.append(st.sec + st.nanosec * 1e-9)
        if len(self.stamps) > 500:
            self.stamps.pop(0)

        if not self.info:
            self.info['frame_id'] = msg.header.frame_id
            if isinstance(msg, Image):
                self.info['size'] = f'{msg.width}x{msg.height}'
                self.info['encoding'] = msg.encoding
                self.info['step'] = msg.step
                self.info['is_bigendian'] = msg.is_bigendian
            elif isinstance(msg, CompressedImage):
                self.info['format'] = msg.format
                self.info['bytes'] = len(msg.data)
            elif isinstance(msg, CameraInfo):
                self.info['size'] = f'{msg.width}x{msg.height}'
                self.info['distortion_model'] = msg.distortion_model
                self.info['K'] = list(msg.k)
                self.info['D'] = list(msg.d)
                self.info['P'] = list(msg.p)

    @property
    def hz(self):
        if self.count < 2 or self.first_wall is None:
            return 0.0
        span = self.last_wall - self.first_wall
        return (self.count - 1) / span if span > 0 else 0.0


class OakdProbe(Node):

    def __init__(self, ns, samples):
        super().__init__('oakd_probe')
        self.ns = ns.rstrip('/')
        self.samples = samples
        self.stats = {}

        discovered = self._discover()
        self._subscribe_all(discovered)

    # ------------------------------------------------------------------
    def _discover(self):
        """그래프에 광고된 /<ns>/oakd/ 토픽 수집."""
        found = {}
        for name, types in self.get_topic_names_and_types():
            if f'{self.ns}/oakd/' in name:
                found[name] = types[0] if types else '?'
        return found

    # ------------------------------------------------------------------
    def _subscribe_all(self, discovered):
        # 1) 그래프에서 발견된 것
        for topic, type_name in discovered.items():
            cls = TYPE_MAP.get(type_name)
            if cls is None:
                # 타입을 모르면 통계만 남기고 구독은 건너뛴다
                self.stats[topic] = TopicStat(topic, type_name, '(구독 불가 타입)')
                continue
            self._add(topic, cls, type_name, '')

        # 2) 후보 토픽 blind subscribe (lazy publisher 대응)
        for suffix, cls, role in CANDIDATES:
            topic = f'{self.ns}/oakd/{suffix}'
            if topic in self.stats:
                self.stats[topic].role = role
                continue
            self._add(topic, cls, cls.__name__, role + ' [blind]')

    def _add(self, topic, cls, type_name, role):
        st = TopicStat(topic, type_name, role)
        self.stats[topic] = st
        # 이미지류는 SensorDataQoS(best_effort) 여야 붙는다.
        self.create_subscription(cls, topic, st.on_msg, qos_profile_sensor_data)

    # ------------------------------------------------------------------
    def rgb_topic(self):
        """실제로 데이터가 들어온 RGB 토픽을 고른다 (preview 우선, 그다음 isp)."""
        for suffix in ('rgb/preview/image_raw',
                       'rgb/preview/image_raw/compressed',
                       'rgb/image_raw/compressed', 'rgb/image_raw'):
            t = f'{self.ns}/oakd/{suffix}'
            if t in self.stats and self.stats[t].count > 0:
                return t
        return None

    def depth_topic(self):
        t = f'{self.ns}/oakd/stereo/image_raw'
        return t if t in self.stats and self.stats[t].count > 0 else None


# ======================================================================
# 출력
# ======================================================================
def print_topics(probe):
    print()
    print('=' * 78)
    print(' 1) OAK-D 토픽 목록')
    print('=' * 78)
    rows = sorted(probe.stats.values(), key=lambda s: s.topic)
    live = [s for s in rows if s.count > 0]
    dead = [s for s in rows if s.count == 0]

    if not live:
        print('  수신된 토픽이 하나도 없습니다.')
    for s in live:
        print(f'  {s.topic}')
        print(f'      타입     : {s.type_name}')
        print(f'      주기     : {s.hz:6.2f} Hz   ({s.count} msgs)')
        print(f'      frame_id : {s.info.get("frame_id", "?")}')
        if 'size' in s.info:
            print(f'      해상도   : {s.info["size"]}')
        if 'encoding' in s.info:
            print(f'      encoding : {s.info["encoding"]}  (step={s.info.get("step")})')
        if 'format' in s.info:
            print(f'      format   : {s.info["format"]}  (평균 {s.info["bytes"]} bytes)')
        print()

    if dead:
        print('  -- 수신 없음 --')
        for s in dead:
            print(f'     {s.topic}   {s.role}')
        print()
        print('  수신이 없다면:')
        print('    - lazy publisher 확인:')
        print(f'        ros2 param get {probe.ns}/oakd rgb.i_enable_lazy_publisher')
        print('    - 강제로 끄기:')
        print(f'        ros2 param set {probe.ns}/oakd rgb.i_enable_lazy_publisher false')
        print(f'        ros2 param set {probe.ns}/oakd stereo.i_enable_lazy_publisher false')
        print('    - 네임스페이스가 맞는지: ros2 node list | grep oakd')


def _fmt_k(k):
    return (f'fx={k[0]:8.2f}  fy={k[4]:8.2f}\n'
            f'                cx={k[2]:8.2f}  cy={k[5]:8.2f}')


def print_camera_info(probe):
    print()
    print('=' * 78)
    print(' 2) camera_info 비교 (RGB vs Depth)')
    print('=' * 78)

    # preview camera_info 가 있으면 그걸, 없으면 isp camera_info 를 쓴다.
    rgb_i = probe.stats.get(f'{probe.ns}/oakd/rgb/preview/camera_info')
    if rgb_i is None or not rgb_i.info.get('K'):
        rgb_i = probe.stats.get(f'{probe.ns}/oakd/rgb/camera_info')
    dep_i = probe.stats.get(f'{probe.ns}/oakd/stereo/camera_info')

    for label, st in (('RGB  ', rgb_i), ('DEPTH', dep_i)):
        print(f'  [{label}]')
        if st is None or not st.info.get('K'):
            print('      camera_info 수신 없음')
            print()
            continue
        k = st.info['K']
        print(f'      해상도   : {st.info["size"]}')
        print(f'      frame_id : {st.info["frame_id"]}')
        print(f'      모델     : {st.info["distortion_model"]}')
        print(f'      K        : {_fmt_k(k)}')
        d = st.info["D"]
        print(f'      D        : {[round(v, 5) for v in d]}')
        print()

    # 좌표 정합에 필요한 비율 계산
    if (rgb_i and rgb_i.info.get('K')) and (dep_i and dep_i.info.get('K')):
        kr, kd = rgb_i.info['K'], dep_i.info['K']
        wr, hr = rgb_i.info['size'].split('x')
        wd, hd = dep_i.info['size'].split('x')
        print('  [좌표 정합 참고]')
        print(f'      해상도 비  : x {int(wd)/int(wr):.4f}   y {int(hd)/int(hr):.4f}')
        print(f'      초점거리 비: fx {kd[0]/kr[0]:.4f}   fy {kd[4]/kr[4]:.4f}')
        print('      위 두 비율이 비슷하면 단순 스케일 방식도 쓸 만하다.')
        print('      크게 다르면 K 행렬 기반(intrinsic) 방식을 써야 한다.')
        print()


def measure_sync(probe, samples, timeout):
    """rgb / depth header.stamp 차이 분포 측정."""
    print()
    print('=' * 78)
    print(f' 3) RGB <-> Depth 타임스탬프 차이 ({samples} 샘플 목표)')
    print('=' * 78)

    rt, dt = probe.rgb_topic(), probe.depth_topic()
    if rt is None or dt is None:
        print(f'  측정 불가 — rgb={rt}  depth={dt}')
        print('  두 토픽 모두 데이터가 들어와야 측정할 수 있습니다.')
        return

    print(f'  RGB  : {rt}')
    print(f'  Depth: {dt}')
    print()

    rgb_st, dep_st = probe.stats[rt], probe.stats[dt]
    diffs = []
    seen = set()
    deadline = time.time() + timeout

    while rclpy.ok() and len(diffs) < samples and time.time() < deadline:
        rclpy.spin_once(probe, timeout_sec=0.05)
        r_list, d_list = list(rgb_st.stamps), list(dep_st.stamps)
        if not r_list or not d_list:
            continue
        # 각 RGB 스탬프에 대해 가장 가까운 Depth 스탬프를 짝지어 차이를 기록
        for r in r_list:
            if r in seen:
                continue
            nearest = min(d_list, key=lambda d: abs(d - r))
            if abs(nearest - r) > 1.0:       # 1초 넘게 벌어지면 짝이 아님
                continue
            seen.add(r)
            diffs.append(nearest - r)
            if len(diffs) >= samples:
                break

    if not diffs:
        print('  짝지을 수 있는 샘플이 없습니다.')
        return

    absd = [abs(x) for x in diffs]
    mean, mx = statistics.mean(absd), max(absd)
    std = statistics.pstdev(absd) if len(absd) > 1 else 0.0
    print(f'  샘플 수   : {len(diffs)}')
    print(f'  |차이| 평균: {mean*1000:8.2f} ms')
    print(f'  |차이| 최대: {mx*1000:8.2f} ms')
    print(f'  |차이| 표준편차: {std*1000:6.2f} ms')
    print(f'  부호       : depth - rgb 평균 {statistics.mean(diffs)*1000:+.2f} ms')
    print()

    # slop 권장값 — 최대치에 여유 50%
    rec = max(0.01, round(mx * 1.5, 3))
    print(f'  >>> 권장 slop: {rec:.3f} s')
    print(f'      (최대 차이 {mx*1000:.1f} ms 에 50% 여유)')
    print('      너무 작으면 동기화 콜백이 거의 안 불리고,')
    print('      너무 크면 시간이 안 맞는 프레임끼리 짝지어져 거리값이 튄다.')


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--ns', default='/robot8', help='로봇 네임스페이스')
    ap.add_argument('--samples', type=int, default=100, help='타임스탬프 샘플 수')
    ap.add_argument('--warmup', type=float, default=8.0, help='토픽 수집 시간(초)')
    ap.add_argument('--timeout', type=float, default=60.0, help='동기화 측정 제한(초)')
    args = ap.parse_args(sys.argv[1:] if sys.argv[1:] else [])

    rclpy.init()
    probe = OakdProbe(args.ns, args.samples)

    print(f'OAK-D 진단 시작 — namespace={probe.ns}')
    print(f'{args.warmup:.0f}초 동안 토픽을 수집합니다...')
    end = time.time() + args.warmup
    while rclpy.ok() and time.time() < end:
        rclpy.spin_once(probe, timeout_sec=0.05)

    try:
        print_topics(probe)
        print_camera_info(probe)
        measure_sync(probe, args.samples, args.timeout)
    finally:
        print()
        print('=' * 78)
        probe.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
