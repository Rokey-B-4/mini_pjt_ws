#!/usr/bin/env python3
"""
mission_manager_node

미션 전체 상태머신. 웹캠 트리거를 받아 undock -> Nav2 주행 -> 근접 접근 순으로
상태를 전이시키고, 상태가 바뀔 때마다 RobotState 를 발행한다.

상태
  IDLE     : /webcam/trigger == True 대기
  UNDOCK   : (도킹 상태면) undock, setInitialPose, waitUntilNav2Active, AMCL 수렴 대기
  NAV      : goToPose 후 isTaskComplete 폴링. 실패 시 nav_retry 만큼 재시도
  APPROACH : cancelTask 로 Nav2 를 확실히 끊고 /approach/enable=True
  DONE     : cmd_vel 0 발행, 최종 상태 발행, use_dock 이면 dock 복귀
  FAILED   : 정지 및 사유 로그

동시성 설계 (중요)
  TurtleBot4Navigator(=BasicNavigator) 의 메서드는 내부에서 rclpy.spin_until_future_complete
  로 '자기 노드'를 스핀한다. 이걸 이 노드의 타이머 콜백에서 직접 부르면 스핀이 중첩되어
  상태 발행/트리거 수신이 멈춘다.
  그래서 navigator 를 만지는 작업은 전부 워커 스레드 하나에서만 실행하고(_submit),
  타이머는 그 결과 플래그만 폴링한다. navigator 노드는 이 프로세스의 executor 에
  절대 추가하지 않는다 (이중 스핀 방지).

cmd_vel 경합
  TurtleBot4(Humble) 에는 twist_mux 가 없고 Nav2 controller_server 가 cmd_vel 로 직접
  발행한다. 즉 Nav2 와 근접 접근 노드가 같은 토픽에 동시에 쓸 수 있다.
  APPROACH 진입 전 cancelTask() 를 호출하고, 실제로 취소됐는지(isTaskComplete + CANCELED)
  확인한 뒤에만 /approach/enable 을 올린다.
"""

import threading
import time

import rclpy
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)

from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from std_msgs.msg import Bool

from mini_pjt_interfaces.msg import RobotState


class S:
    """상태 문자열."""

    IDLE = 'IDLE'
    UNDOCK = 'UNDOCK'
    SEARCH = 'SEARCH'      # 언도킹 후 제자리에서 Car 를 찾는다 (임시 목표 주행 없음)
    NAV = 'NAV'            # (구) 목표좌표 주행 — 현재 미사용
    APPROACH = 'APPROACH'
    DONE = 'DONE'
    FAILED = 'FAILED'


class MissionManagerNode(Node):

    def __init__(self):
        super().__init__('mission_manager_node')

        # ── 파라미터 ──────────────────────────────────────────
        self.declare_parameter('robot_namespace', '/robot8')
        self.declare_parameter('dry_run', False)
        self.declare_parameter('use_dock', True)

        # [x(m), y(m), yaw(deg)] — map 프레임 기준.
        # yaw 는 '도' 단위다. TurtleBot4Navigator.getPoseStamped() 가 도를 받는다.
        self.declare_parameter('initial_pose', [0.0, 0.0, 0.0])
        self.declare_parameter('goal_pose', [0.0, 0.0, 0.0])

        self.declare_parameter('nav_retry', 2)
        self.declare_parameter('nav_timeout_sec', 180.0)
        self.declare_parameter('undock_timeout_sec', 60.0)
        self.declare_parameter('cancel_timeout_sec', 10.0)
        self.declare_parameter('approach_timeout_sec', 60.0)

        # AMCL 수렴 판정: /amcl_pose 공분산(6x6 row-major)
        #   cov[0]=x 분산, cov[7]=y 분산, cov[35]=yaw 분산
        self.declare_parameter('amcl_wait_sec', 30.0)
        self.declare_parameter('amcl_cov_xy_max', 0.05)     # m^2
        self.declare_parameter('amcl_cov_yaw_max', 0.06)    # rad^2
        self.declare_parameter('amcl_required_hits', 3)     # 연속 N회 만족해야 수렴 인정

        self.declare_parameter('tick_rate_hz', 5.0)
        self.declare_parameter('state_publish_rate_hz', 2.0)

        # ── Car 접근(cmd_vel 전환) ──
        # target_seeker_node 가 Car 를 map 좌표로 추적하고 /robot/seeking(Bool)을 낸다.
        # NAV(목적지 주행) 중 seeking 이 뜨면 Nav2 를 끊고 APPROACH(cmd_vel 접근)로 전환한다.
        self.declare_parameter('seek_enable', True)
        self.declare_parameter('seeking_topic', '/robot/seeking')

        # SEARCH: 언도킹 후 임시 목표 없이 제자리에서 Car 를 찾는다.
        self.declare_parameter('search_rotate', True)        # 제자리 회전하며 탐색
        self.declare_parameter('search_angular', 0.3)        # rad/s
        self.declare_parameter('search_timeout_sec', 60.0)   # 못 찾으면 실패 (0=무한)

        self.declare_parameter('trigger_topic', '/webcam/trigger')
        self.declare_parameter('state_topic', '/robot/state')
        self.declare_parameter('approach_enable_topic', '/approach/enable')
        # 근접 접근 노드가 도달을 알리는 토픽(RobotState.arrived).
        # /robot/state 는 이 노드의 출력이라 발행자가 겹치지 않게 분리했다.
        self.declare_parameter('approach_status_topic', '/approach/status')

        self.ns = str(self.get_parameter('robot_namespace').value).rstrip('/')
        self.dry_run = bool(self.get_parameter('dry_run').value)
        self.use_dock = bool(self.get_parameter('use_dock').value)
        self.nav_retry = int(self.get_parameter('nav_retry').value)

        # ── QoS ───────────────────────────────────────────────
        # trigger 는 webcam_detector_node 가 TRANSIENT_LOCAL 로 발행한다.
        # 구독도 TRANSIENT_LOCAL 이어야 늦게 떠도 마지막 값을 받는다.
        qos_trigger = QoSProfile(depth=1)
        qos_trigger.reliability = ReliabilityPolicy.RELIABLE
        qos_trigger.durability = DurabilityPolicy.TRANSIENT_LOCAL

        # AMCL 은 TRANSIENT_LOCAL + RELIABLE 로 발행한다 (nav2_simple_commander 와 동일).
        qos_amcl = QoSProfile(depth=1)
        qos_amcl.reliability = ReliabilityPolicy.RELIABLE
        qos_amcl.durability = DurabilityPolicy.TRANSIENT_LOCAL
        qos_amcl.history = HistoryPolicy.KEEP_LAST

        # ── 퍼블리셔 / 구독 ───────────────────────────────────
        self.state_pub = self.create_publisher(
            RobotState, self.get_parameter('state_topic').value, 10)
        self.approach_enable_pub = self.create_publisher(
            Bool, self.get_parameter('approach_enable_topic').value, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, f'{self.ns}/cmd_vel', 10)

        self.create_subscription(
            Bool, self.get_parameter('trigger_topic').value,
            self._trigger_cb, qos_trigger)
        self.create_subscription(
            RobotState, self.get_parameter('approach_status_topic').value,
            self._approach_status_cb, 10)
        self.create_subscription(
            PoseWithCovarianceStamped, f'{self.ns}/amcl_pose',
            self._amcl_cb, qos_amcl)

        # Car 를 보면 NAV 를 끊고 cmd_vel 접근(APPROACH)으로 전환
        self.seek_enable = bool(self.get_parameter('seek_enable').value)
        self.search_rotate = bool(self.get_parameter('search_rotate').value)
        self.search_angular = float(self.get_parameter('search_angular').value)
        self.search_timeout = float(self.get_parameter('search_timeout_sec').value)
        self.create_subscription(
            Bool, self.get_parameter('seeking_topic').value, self._seeking_cb, 10)

        # ── 내부 상태 ─────────────────────────────────────────
        self._lock = threading.Lock()
        self.state = S.IDLE
        self.reason = ''
        self.target_distance = -1.0
        self.arrived = False
        self.trigger = False
        self.nav_attempt = 0

        self._amcl_cov = None           # (var_x, var_y, var_yaw)
        self._amcl_stamp = 0.0

        self._seeking = False           # target_seeker 가 Car 를 확인했는가

        self._job_name = None
        self._job_done = False
        self._job_ok = False
        self._job_msg = ''
        self._job_thread = None

        self.navigator = None

        # ── 타이머 ────────────────────────────────────────────
        self.create_timer(1.0 / float(self.get_parameter('tick_rate_hz').value), self._tick)
        self.create_timer(
            1.0 / float(self.get_parameter('state_publish_rate_hz').value),
            self._publish_state)

        self.get_logger().info(
            f'mission_manager_node 시작 | ns={self.ns} dry_run={self.dry_run} '
            f'use_dock={self.use_dock} nav_retry={self.nav_retry}')
        if self.dry_run:
            self.get_logger().warn(
                'dry_run=True — Nav2/dock 을 실제로 호출하지 않고 상태 전이만 시뮬레이션합니다.')
        self._publish_state()

    # ==================================================================
    # 콜백
    # ==================================================================
    def _trigger_cb(self, msg):
        self.trigger = bool(msg.data)

    def _approach_status_cb(self, msg):
        self.target_distance = float(msg.target_distance)
        if msg.arrived:
            self.arrived = True

    def _amcl_cb(self, msg):
        cov = msg.pose.covariance
        with self._lock:
            self._amcl_cov = (float(cov[0]), float(cov[7]), float(cov[35]))
            self._amcl_stamp = time.time()

    def _seeking_cb(self, msg):
        self._seeking = bool(msg.data)

    # ==================================================================
    # 상태 관리
    # ==================================================================
    def _set_state(self, new_state, reason=''):
        if new_state == self.state:
            return
        self.get_logger().info(f'[상태] {self.state} -> {new_state}'
                               + (f' ({reason})' if reason else ''))
        self.state = new_state
        self.reason = reason
        self._publish_state()

    def _publish_state(self):
        msg = RobotState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.ns.lstrip('/') or 'robot'
        msg.state = self.state
        msg.target_distance = float(self.target_distance)
        msg.arrived = bool(self.arrived)
        self.state_pub.publish(msg)

    def _set_approach_enable(self, enable):
        self.approach_enable_pub.publish(Bool(data=bool(enable)))

    def _publish_zero_cmd_vel(self, times=5):
        """정지 명령을 여러 번 보낸다 (best-effort 유실 대비)."""
        for _ in range(times):
            self.cmd_vel_pub.publish(Twist())

    # ==================================================================
    # 워커 스레드 (navigator 는 여기서만 만진다)
    # ==================================================================
    def _submit(self, name, fn):
        """navigator 블로킹 작업을 워커 스레드로 넘긴다."""
        self._job_name = name
        self._job_done = False
        self._job_ok = False
        self._job_msg = ''

        def runner():
            try:
                ok, msg = fn()
            except Exception as e:                      # noqa: BLE001
                ok, msg = False, f'{type(e).__name__}: {e}'
                self.get_logger().error(f'[{name}] 예외: {msg}')
            self._job_ok = ok
            self._job_msg = msg
            self._job_done = True

        self._job_thread = threading.Thread(target=runner, name=f'job-{name}', daemon=True)
        self._job_thread.start()
        self.get_logger().info(f'[작업] {name} 시작')

    def _job_running(self):
        return self._job_name is not None and not self._job_done

    def _take_job_result(self):
        """완료된 작업 결과를 회수하고 슬롯을 비운다."""
        name, ok, msg = self._job_name, self._job_ok, self._job_msg
        self._job_name = None
        self._job_done = False
        self.get_logger().info(f'[작업] {name} 완료 — {"성공" if ok else "실패"}'
                               + (f' ({msg})' if msg else ''))
        return ok, msg

    # ------------------------------------------------------------------
    def _ensure_navigator(self):
        if self.navigator is not None:
            return self.navigator
        from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator
        self.navigator = TurtleBot4Navigator(namespace=self.ns)
        return self.navigator

    def _pose(self, xyyaw):
        nav = self._ensure_navigator()
        # getPoseStamped 의 rotation 은 '도' 단위다.
        return nav.getPoseStamped([float(xyyaw[0]), float(xyyaw[1])], float(xyyaw[2]))

    # ==================================================================
    # AMCL 수렴 대기
    # ==================================================================
    def wait_for_amcl_convergence(self, timeout_sec=None):
        """
        /amcl_pose 공분산이 임계값 이하로 떨어질 때까지 대기한다.

        공분산은 6x6 row-major 이며 cov[0]=x분산, cov[7]=y분산, cov[35]=yaw분산.
        초기 pose 를 막 뿌린 직후에는 파티클이 퍼져 있어 분산이 크다.
        연속 amcl_required_hits 회 임계 이하일 때만 수렴으로 인정한다
        (한 프레임 우연히 낮게 나오는 경우를 걸러낸다).

        워커 스레드에서 호출한다. 이 노드는 메인 스레드가 스핀하므로
        여기서는 spin 하지 않고 콜백이 갱신한 값을 폴링하기만 한다.

        :return: (성공여부, 메시지)
        """
        if timeout_sec is None:
            timeout_sec = float(self.get_parameter('amcl_wait_sec').value)
        xy_max = float(self.get_parameter('amcl_cov_xy_max').value)
        yaw_max = float(self.get_parameter('amcl_cov_yaw_max').value)
        need = int(self.get_parameter('amcl_required_hits').value)

        deadline = time.time() + timeout_sec
        hits = 0
        last = None

        while time.time() < deadline:
            if not rclpy.ok():
                return False, 'shutdown'
            with self._lock:
                cov = self._amcl_cov
                age = time.time() - self._amcl_stamp if self._amcl_stamp else None

            if cov is not None and age is not None and age < 5.0:
                last = cov
                if cov[0] <= xy_max and cov[1] <= xy_max and cov[2] <= yaw_max:
                    hits += 1
                    if hits >= need:
                        self.get_logger().info(
                            f'AMCL 수렴 — var_x={cov[0]:.4f} var_y={cov[1]:.4f} '
                            f'var_yaw={cov[2]:.4f}')
                        return True, 'converged'
                else:
                    hits = 0
            time.sleep(0.2)

        if last is None:
            return False, f'{timeout_sec:.0f}s 동안 {self.ns}/amcl_pose 를 한 번도 못 받음'
        return False, (f'AMCL 미수렴 (var_x={last[0]:.4f} var_y={last[1]:.4f} '
                       f'var_yaw={last[2]:.4f}, 임계 xy<={xy_max} yaw<={yaw_max})')

    # ==================================================================
    # 작업 구현 (전부 워커 스레드에서 실행)
    # ==================================================================
    def _job_undock(self):
        """undock -> setInitialPose -> waitUntilNav2Active -> AMCL 수렴."""
        if self.dry_run:
            time.sleep(2.0)
            return True, 'dry_run'

        nav = self._ensure_navigator()
        timeout = float(self.get_parameter('undock_timeout_sec').value)

        if self.use_dock:
            docked = nav.getDockedStatus()
            self.get_logger().info(f'도킹 상태: {docked}')
            if docked:
                nav.undock_send_goal()
                deadline = time.time() + timeout
                while not nav.isUndockComplete():
                    if time.time() > deadline:
                        return False, f'undock 이 {timeout:.0f}s 안에 끝나지 않음'
                    time.sleep(0.1)
                self.get_logger().info('undock 완료')
            else:
                self.get_logger().info('이미 언도킹 상태 — undock 생략')

        # 초기 pose 주입
        init = list(self.get_parameter('initial_pose').value)
        nav.setInitialPose(self._pose(init))
        self.get_logger().info(f'초기 pose 발행: x={init[0]} y={init[1]} yaw={init[2]}deg')

        # Nav2 활성 대기 (블로킹이지만 워커 스레드라 본 노드 스핀은 유지된다)
        nav.waitUntilNav2Active()
        self.get_logger().info('Nav2 활성 확인')

        # AMCL 수렴 대기
        ok, msg = self.wait_for_amcl_convergence()
        if not ok:
            return False, msg
        return True, 'ready'

    # ------------------------------------------------------------------
    def _job_nav(self):
        """
        목적지(goal_pose)로 Nav2 주행. 단 주행 중 target_seeker 가 Car 를 확인하면
        (/robot/seeking) Nav2 를 끊고 'car_seen' 으로 복귀 -> APPROACH(cmd_vel 접근)로 전환.
        """
        if self.dry_run:
            time.sleep(3.0)
            return True, 'dry_run'

        from nav2_simple_commander.robot_navigator import TaskResult

        nav = self._ensure_navigator()
        goal = list(self.get_parameter('goal_pose').value)
        timeout = float(self.get_parameter('nav_timeout_sec').value)

        nav.goToPose(self._pose(goal))
        self.get_logger().info(
            f'목적지 이동 시작: x={goal[0]:.2f} y={goal[1]:.2f} yaw={goal[2]:.0f}deg')

        deadline = time.time() + timeout
        while not nav.isTaskComplete():
            if not rclpy.ok():
                return False, 'shutdown'
            if time.time() > deadline:
                nav.cancelTask()
                return False, f'주행이 {timeout:.0f}s 를 초과해 취소함'

            # Car 발견 -> Nav2 중단하고 cmd_vel 접근으로 전환
            if self.seek_enable and self._seeking:
                nav.cancelTask()
                self.get_logger().info('Car 발견 — Nav2 중단, cmd_vel 접근으로 전환')
                return True, 'car_seen'

            fb = nav.getFeedback()
            if fb is not None:
                remain = getattr(fb, 'distance_remaining', None)
                if remain is not None:
                    self.get_logger().info(
                        f'남은 거리 {remain:.2f} m', throttle_duration_sec=3.0)
            time.sleep(0.2)

        result = nav.getResult()
        if result == TaskResult.SUCCEEDED:
            return True, 'succeeded'
        if result == TaskResult.CANCELED:
            return False, 'canceled'
        return False, f'failed ({result})'

    # ------------------------------------------------------------------
    def _job_cancel_nav(self):
        """
        Nav2 를 확실히 끊는다.

        cancelTask() 만 부르고 넘어가면 controller_server 가 마지막 cmd_vel 을
        더 보낼 수 있어 수동 제어와 겹친다. isTaskComplete() 가 True 가 될 때까지
        확인하고, 정지 명령까지 보낸 뒤에 성공으로 친다.
        """
        if self.dry_run:
            time.sleep(0.5)
            self._publish_zero_cmd_vel()
            return True, 'dry_run'

        nav = self._ensure_navigator()
        timeout = float(self.get_parameter('cancel_timeout_sec').value)

        nav.cancelTask()

        deadline = time.time() + timeout
        while not nav.isTaskComplete():
            if time.time() > deadline:
                return False, f'cancelTask 후 {timeout:.0f}s 안에 취소가 확인되지 않음'
            time.sleep(0.1)

        # 취소 결과 확인 (이미 도착해서 SUCCEEDED 로 끝난 경우도 정상으로 본다)
        from nav2_simple_commander.robot_navigator import TaskResult
        result = nav.getResult()
        self.get_logger().info(f'Nav2 태스크 종료 확인: {result}')

        # 잔여 속도 명령 제거
        self._publish_zero_cmd_vel()
        time.sleep(0.3)
        self._publish_zero_cmd_vel()
        return True, str(result)

    # ------------------------------------------------------------------
    def _job_dock(self):
        if self.dry_run:
            time.sleep(1.0)
            return True, 'dry_run'
        nav = self._ensure_navigator()
        nav.dock_send_goal()
        deadline = time.time() + 120.0
        while not nav.isDockComplete():
            if time.time() > deadline:
                return False, 'dock 타임아웃'
            time.sleep(0.2)
        return True, 'docked'

    # ==================================================================
    # 상태머신
    # ==================================================================
    def _tick(self):
        if self._job_running():
            return

        handler = {
            S.IDLE: self._tick_idle,
            S.UNDOCK: self._tick_undock,
            S.SEARCH: self._tick_search,
            S.APPROACH: self._tick_approach,
            S.DONE: self._tick_done,
            S.FAILED: self._tick_failed,
        }.get(self.state)
        if handler:
            handler()

    # ------------------------------------------------------------------
    def _tick_idle(self):
        if self._job_name is not None:
            self._take_job_result()
        if self.trigger:
            self.arrived = False
            self.nav_attempt = 0
            self._set_state(S.UNDOCK, 'webcam trigger 수신')
            self._submit('undock', self._job_undock)

    # ------------------------------------------------------------------
    def _tick_undock(self):
        if self._job_name is None:
            return
        ok, msg = self._take_job_result()
        if ok:
            # 임시 목표 주행 없이 바로 제자리 탐색으로 간다.
            self._search_start = time.time()
            self._set_state(S.SEARCH, '기동 완료 — Car 탐색 시작')
        else:
            self._fail(f'UNDOCK 실패: {msg}')

    # ------------------------------------------------------------------
    def _tick_search(self):
        """
        언도킹 후: 임시 목표로 가지 않고 제자리에서 Car 를 찾는다.
        온보드 YOLO 가 Car 를 확인(/robot/seeking)하면 즉시 APPROACH(cmd_vel 접근)로 전환.
          - search_rotate=True : 제자리 회전하며 탐색
          - search_rotate=False: 정지한 채 시야에 들어오길 대기
        """
        # Car 발견 → 접근 시작 (Nav2 취소 불필요: 주행 목표를 안 썼다)
        if self._seeking:
            self._publish_zero_cmd_vel()                    # 탐색 회전 정지
            self._set_approach_enable(True)                 # car_approach 활성화
            self._approach_deadline = time.time() + float(
                self.get_parameter('approach_timeout_sec').value)
            self._set_state(S.APPROACH, 'Car 발견 → 접근')
            return

        # 탐색 동작: 제자리 회전 또는 대기
        if self.search_rotate:
            twist = Twist()
            twist.angular.z = self.search_angular
            self.cmd_vel_pub.publish(twist)

        # 탐색 타임아웃
        elapsed = time.time() - getattr(self, '_search_start', time.time())
        if self.search_timeout > 0 and elapsed > self.search_timeout:
            self._publish_zero_cmd_vel()
            self._fail(f'SEARCH 타임아웃 — {self.search_timeout:.0f}s 안에 Car 를 찾지 못함')

    # ------------------------------------------------------------------
    def _tick_approach(self):
        # 접근 활성화(/approach/enable=True)와 deadline 은 SEARCH->APPROACH 전이에서 이미 설정됨.
        # car_approach_node 가 map 좌표로 cmd_vel 접근 -> 도달하면 /approach/status.arrived.
        if self.arrived:
            self._set_approach_enable(False)
            self._set_state(S.DONE, '목표 도달')
            return

        if time.time() > getattr(self, '_approach_deadline', 0.0):
            self._set_approach_enable(False)
            self._fail('APPROACH 타임아웃 — 목표에 도달하지 못했습니다')

    # ------------------------------------------------------------------
    def _tick_done(self):
        if self._job_name is not None:
            self._take_job_result()
            self.get_logger().info('미션 완료')
            return

        # DONE 진입 직후 1회만 처리
        if not getattr(self, '_done_handled', False):
            self._done_handled = True
            self._set_approach_enable(False)
            self._publish_zero_cmd_vel()
            self.get_logger().info('정지 명령 발행')
            if self.use_dock:
                self._submit('dock', self._job_dock)

    # ------------------------------------------------------------------
    def _tick_failed(self):
        if self._job_name is not None:
            self._take_job_result()

    # ------------------------------------------------------------------
    def _fail(self, reason):
        self._set_approach_enable(False)
        self._publish_zero_cmd_vel()
        self.get_logger().error(reason)
        self._set_state(S.FAILED, reason)

    # ------------------------------------------------------------------
    def destroy_node(self):
        try:
            self._set_approach_enable(False)
            self._publish_zero_cmd_vel(times=3)
        except Exception:                               # noqa: BLE001
            pass
        if self.navigator is not None:
            try:
                self.navigator.destroy_node()
            except Exception:                           # noqa: BLE001
                pass
            self.navigator = None
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    executor = None
    try:
        node = MissionManagerNode()
        # ★ 본 노드는 '전용' executor 로 스핀한다.
        # rclpy.spin() 은 전역(global) executor 를 쓰는데, TurtleBot4Navigator 의
        # spin_until_future_complete() 도 전역 executor 를 쓴다. 워커 스레드에서 navigator 를
        # 호출하는 동안 메인 스레드가 같은 전역 executor 를 스핀하면 wait set 이 깨져
        # 'wait set index too big' 로 죽는다. 전용 executor 로 분리하면 충돌하지 않는다.
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:                                   # noqa: BLE001
        if rclpy.ok():
            raise
    finally:
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
