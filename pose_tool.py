#!/usr/bin/env python3
"""
pose_tool — RViz2 에서 찍은 pose 를 params.yaml 에 바로 붙일 형식으로 뽑아준다.

쿼터니언을 손으로 도(degree)로 바꾸다 라디안과 헷갈리는 실수를 막기 위한 도구다.

사용법
  # 목표 지점: RViz2 의 '2D Goal Pose' 로 찍으면 출력됨
  ./pose_tool.py goal

  # 현재 위치(독 위치 등): AMCL 이 추정한 값을 읽음
  ./pose_tool.py amcl

  # 임의 토픽 지정
  ./pose_tool.py --topic /robot8/goal_pose --type PoseStamped

  # 계속 찍어보기 (Ctrl-C 로 종료)
  ./pose_tool.py amcl --watch

옵션
  --ns    로봇 네임스페이스 (기본 /robot8)
"""

import argparse
import math
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped


def yaw_deg_from_quat(z, w):
    """평면 주행이므로 z, w 만으로 yaw 를 구한다."""
    return math.degrees(2.0 * math.atan2(z, w))


class PoseTool(Node):

    def __init__(self, topic, msg_type, watch):
        super().__init__('pose_tool')
        self.watch = watch
        self.got = False

        if msg_type is PoseWithCovarianceStamped:
            # AMCL 은 TRANSIENT_LOCAL + RELIABLE 로 발행한다.
            qos = QoSProfile(depth=1)
            qos.reliability = ReliabilityPolicy.RELIABLE
            qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        else:
            qos = 10

        self.create_subscription(msg_type, topic, self._cb, qos)
        print(f'구독 중: {topic}')
        if msg_type is PoseStamped:
            print("RViz2 에서 '2D Goal Pose' 로 목표를 찍으세요.")
            print('※ Nav2 가 떠 있으면 로봇이 실제로 그 지점으로 출발합니다.')
        print()

    def _cb(self, msg):
        pose = msg.pose.pose if hasattr(msg.pose, 'pose') else msg.pose
        x = pose.position.x
        y = pose.position.y
        yaw = yaw_deg_from_quat(pose.orientation.z, pose.orientation.w)

        print(f'  x   = {x:.4f} m')
        print(f'  y   = {y:.4f} m')
        print(f'  yaw = {yaw:.2f} deg   (quat z={pose.orientation.z:.6f}, '
              f'w={pose.orientation.w:.6f})')

        if hasattr(msg.pose, 'covariance'):
            c = msg.pose.covariance
            conv = 'O 수렴' if (c[0] <= 0.05 and c[7] <= 0.05 and c[35] <= 0.06) else 'X 미수렴'
            print(f'  공분산: var_x={c[0]:.4f} var_y={c[7]:.4f} var_yaw={c[35]:.4f}  -> {conv}')

        print()
        print('  params.yaml 에 붙여넣기:')
        print(f'    [{x:.4f}, {y:.4f}, {yaw:.2f}]')
        print()
        self.got = True


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('preset', nargs='?', choices=['goal', 'amcl'],
                    help='goal=2D Goal Pose 읽기 / amcl=현재 추정 위치 읽기')
    ap.add_argument('--ns', default='/robot8')
    ap.add_argument('--topic', default=None)
    ap.add_argument('--type', default=None, choices=['PoseStamped', 'PoseWithCovarianceStamped'])
    ap.add_argument('--watch', action='store_true', help='한 번만 읽지 않고 계속 출력')
    args = ap.parse_args()

    ns = args.ns.rstrip('/')

    if args.topic:
        topic = args.topic
        msg_type = (PoseWithCovarianceStamped
                    if args.type == 'PoseWithCovarianceStamped' else PoseStamped)
    elif args.preset == 'goal':
        topic, msg_type = f'{ns}/goal_pose', PoseStamped
    elif args.preset == 'amcl':
        topic, msg_type = f'{ns}/amcl_pose', PoseWithCovarianceStamped
    else:
        ap.print_help()
        return 1

    rclpy.init()
    node = PoseTool(topic, msg_type, args.watch)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.2)
            if node.got and not args.watch:
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
