# README_nav — 맵 작성 / 좌표 취득 / cmd_vel 경합

TurtleBot4 + 웹캠 비전 미니 프로젝트의 Nav2 관련 운영 문서.
로봇 네임스페이스는 `robot8`, `ROS_DOMAIN_ID=8`, 맵은 `basic_map` 을 쓴다.

---

## 0. 매 터미널 공통 준비

source 순서가 중요하다. 뒤에 source 한 것이 앞을 덮어쓴다.

```bash
source /opt/ros/humble/setup.bash && source ~/turtlebot4_ws/install/setup.bash && source /etc/turtlebot4_discovery/setup.bash && source ~/mini_pjt_ws/install/setup.bash
```

> **주의:** `/etc/turtlebot4_discovery/setup.bash` 는 `[ -t 0 ]` 로 TTY 를 검사해서
> 비대화형 셸(스크립트·에디터·launch)에서는 `ROS_SUPER_CLIENT=False` 가 된다.
> 이 경우 Discovery Server 가 알려주는 것만 보여 토픽이 부분적으로만 보인다.
> **반드시 실제 터미널에서 실행할 것.**

연결 확인:

```bash
cd ~/mini_pjt_ws && ./check_env.sh robot8
```

---

## 1. SLAM 으로 맵 만들기

이미 `basic_map` 이 있으므로 **새로 만들 필요는 없다.** 주행 환경이 바뀌었을 때만 수행한다.

### 1-1. 로봇을 독에서 내리고 SLAM 기동

터미널 A — SLAM:

```bash
ros2 launch turtlebot4_navigation slam.launch.py namespace:=/robot8
```

터미널 B — RViz2 (맵이 그려지는 것을 보며 주행):

```bash
ros2 launch turtlebot4_viz view_robot.launch.py namespace:=/robot8
```

터미널 C — 텔레옵으로 환경을 한 바퀴 돈다:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r __ns:=/robot8
```

주행 요령
- 벽을 따라 천천히, 한 방향으로 한 바퀴.
- 출발점으로 되돌아와 루프를 닫으면 오차가 크게 줄어든다.
- 급회전은 스캔 정합을 깨뜨린다. 회전은 특히 천천히.

### 1-2. 맵 저장

RViz2 에서 맵이 충분히 채워졌으면:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/mini_pjt_ws/src/mini_pjt_bringup/maps/basic_map --ros-args -r __ns:=/robot8
```

`basic_map.pgm` 과 `basic_map.yaml` 두 개가 생긴다. 저장 후 빌드해야 `install/` 에 반영된다.

```bash
cd ~/mini_pjt_ws && colcon build --packages-select mini_pjt_bringup --symlink-install
```

`basic_map.yaml` 내용 (현재 값):

```yaml
image: basic_map.pgm
mode: trinary
resolution: 0.05        # 1 픽셀 = 5 cm
origin: [-6.12, -1.01, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

---

## 2. Localization + Nav2 기동 (미션 실행 전 필수)

`mission_manager_node` 는 Nav2 를 **띄우지 않는다.** 이미 떠 있는 Nav2 에 목표만 보낸다.
따라서 미션 전에 아래 두 개를 먼저 올려야 한다.

터미널 A — Localization (AMCL + map_server):

```bash
ros2 launch turtlebot4_navigation localization.launch.py namespace:=/robot8 map:=$HOME/mini_pjt_ws/src/mini_pjt_bringup/maps/basic_map.yaml
```

터미널 B — Nav2:

```bash
ros2 launch turtlebot4_navigation nav2.launch.py namespace:=/robot8
```

터미널 C — RViz2:

```bash
ros2 launch turtlebot4_viz view_robot.launch.py namespace:=/robot8
```

확인:

```bash
ros2 topic list | grep -E "robot8/(map|amcl_pose|initialpose)"
```

세 개가 다 보여야 한다. 안 보이면 Nav2 가 아직 안 뜬 것이다.

---

## 3. RViz2 에서 목표 좌표 뽑아 params.yaml 에 넣기

### 3-1. 좌표 확인용 echo 를 먼저 띄운다

목표 지점용 (`2D Goal Pose` 툴이 발행):

```bash
ros2 topic echo /robot8/goal_pose --once
```

초기 위치(독 위치) 확인용 — AMCL 이 추정한 현재 위치를 읽는다:

```bash
ros2 topic echo /robot8/amcl_pose --once
```

단순히 바닥의 한 점만 찍고 싶으면 (`Publish Point` 툴):

```bash
ros2 topic echo /robot8/clicked_point --once
```

### 3-2. RViz2 에서 찍기

- **초기 위치**: 로봇을 독에 올려둔 상태에서 `2D Pose Estimate` 로 실제 위치·방향을 찍는다.
  그 뒤 `ros2 topic echo /robot8/amcl_pose --once` 로 수렴한 값을 읽는다.
- **목표 지점**: `2D Goal Pose` 로 원하는 지점을 찍고 `ros2 topic echo /robot8/goal_pose --once` 로 읽는다.
  (이때 로봇이 실제로 출발하므로, 좌표만 뽑고 싶으면 Nav2 를 끄고 하거나 바로 취소한다.)

### 3-3. 쿼터니언 → yaw(도) 변환

echo 결과는 쿼터니언이다:

```yaml
position:  {x: -1.55069, y: 0.0668084, z: 0.0}
orientation: {x: 0.0, y: 0.0, z: -0.962154, w: 0.272507}
```

`params.yaml` 의 `initial_pose` / `goal_pose` 는 **`[x, y, yaw(도)]`** 형식이다.
`TurtleBot4Navigator.getPoseStamped()` 가 도 단위를 받기 때문이다.

변환:

```bash
python3 -c "import math; z,w=-0.962154,0.272507; print(round(math.degrees(2*math.atan2(z,w)),2))"
```

위 예시는 `-148.37` 도가 나온다. 그러면:

```yaml
goal_pose: [-1.55069, 0.0668084, -148.37]
```

> **흔한 실수:** 기존 예제 코드에 `getPoseStamped([-1.55069, 0.0668084], -2.5896)` 처럼
> **라디안 값을 그대로 넣은 것**이 있다. `-2.5896 rad` 를 넣으면 `-2.59도` 로 해석되어
> 약 146도가 어긋난다. 반드시 도로 변환해서 넣을 것.

참고로 `TurtleBot4Directions` 도 도 단위다:
`NORTH=0, NORTH_WEST=45, WEST=90, SOUTH_WEST=135, SOUTH=180, SOUTH_EAST=225, EAST=270, NORTH_EAST=315`

### 3-4. params.yaml 반영

`src/mini_pjt_bringup/config/params.yaml` 의 `mission_manager_node` 블록:

```yaml
mission_manager_node:
  ros__parameters:
    initial_pose: [0.0, 0.0, 0.0]      # 독 위치 [x, y, yaw(도)]
    goal_pose:    [-1.55, 0.067, -148.37]
```

`--symlink-install` 로 빌드했으면 yaml 은 심볼릭 링크라 **재빌드 없이** 노드만 재시작하면 된다.

---

## 4. cmd_vel 경합 — twist_mux 확인 결과

### 4-1. 이 로봇에는 twist_mux 가 없다

`turtlebot4_ws/src` 전체를 확인한 결과 twist_mux 설정 파일이 없다.
`turtlebot4_navigation/config/nav2.yaml` 에도 `cmd_vel` 리맵이 없어,
**Nav2 `controller_server` 가 `/robot8/cmd_vel` 로 직접 발행**한다.

즉 다음 셋이 **같은 토픽**을 쓴다:

| 발행자 | 토픽 |
|---|---|
| Nav2 controller_server | `/robot8/cmd_vel` |
| `approach_controller` (근접 접근) | `/robot8/cmd_vel` |
| teleop / joy | `/robot8/cmd_vel` |

우선순위 중재자가 없으므로 **동시에 쓰면 두 명령이 번갈아 들어가 로봇이 떨거나 폭주한다.**

### 4-2. 그래서 APPROACH 진입 전에 반드시 cancelTask()

`mission_manager_node` 는 이렇게 처리한다 (`_job_cancel_nav`):

1. `navigator.cancelTask()` 호출
2. `isTaskComplete()` 가 True 가 될 때까지 폴링 (`cancel_timeout_sec`, 기본 10초)
3. `getResult()` 로 종료 상태 로그
4. zero `Twist` 를 두 번에 나눠 발행해 잔여 명령 제거
5. **여기까지 성공해야** `/approach/enable = True` 를 올린다

취소 확인에 실패하면 `FAILED` 로 가고 수동 제어를 시작하지 않는다.
Nav2 가 살아있는 채로 수동 cmd_vel 을 쏘는 상황을 만들지 않기 위함이다.

### 4-3. 확인 방법

APPROACH 중 `/robot8/cmd_vel` 발행자가 몇 개인지 본다:

```bash
ros2 topic info /robot8/cmd_vel -v
```

`Publisher count` 가 2 이상이고 그중 하나가 `controller_server` 면 취소가 안 된 것이다.

### 4-4. 정말로 분리하고 싶다면 (선택)

경합을 구조적으로 막으려면 twist_mux 를 넣고 Nav2 출력을 별도 토픽으로 뺀다.

Nav2 쪽 리맵 — `nav2.launch.py` 실행 시:

```bash
ros2 launch turtlebot4_navigation nav2.launch.py namespace:=/robot8 -r /robot8/cmd_vel:=/robot8/cmd_vel_nav
```

`approach_controller` 는 별도 토픽으로:

```yaml
approach_controller:
  ros__parameters:
    cmd_vel_topic: "/robot8/cmd_vel_approach"
```

twist_mux 설정 예 (`config/twist_mux.yaml`):

```yaml
twist_mux:
  ros__parameters:
    topics:
      approach:
        topic: cmd_vel_approach
        timeout: 0.5
        priority: 100      # 근접 접근이 최우선
      navigation:
        topic: cmd_vel_nav
        timeout: 0.5
        priority: 50
      joystick:
        topic: cmd_vel_joy
        timeout: 0.5
        priority: 10
```

```bash
ros2 run twist_mux twist_mux --ros-args --params-file config/twist_mux.yaml -r __ns:=/robot8 -r cmd_vel_out:=/robot8/cmd_vel
```

> 이번 프로젝트는 **cancelTask() 확인 방식으로 충분**하다. twist_mux 는 여러 제어원이
> 상시 공존할 때 의미가 있는데, 우리는 Nav2 와 접근 제어가 시간적으로 분리되어 있다.
> 위 설정은 나중에 필요해질 때를 위한 참고다.

---

## 5. 미션 실행

### 5-1. dry_run (로봇 없이 상태머신만)

```bash
ros2 run mini_pjt_control mission_manager_node --ros-args --params-file ~/mini_pjt_ws/install/mini_pjt_bringup/share/mini_pjt_bringup/config/params.yaml
```

트리거를 수동으로 쏜다 (QoS 를 맞춰야 한다):

```bash
ros2 topic pub --once /webcam/trigger std_msgs/msg/Bool "{data: true}" --qos-durability transient_local --qos-reliability reliable
```

도달 보고 흉내:

```bash
ros2 topic pub --once /approach/status mini_pjt_interfaces/msg/RobotState "{state: APPROACHING, target_distance: 0.28, arrived: true}"
```

상태 관찰:

```bash
ros2 topic echo /robot/state
```

### 5-2. 실기 (Nav2 가 떠 있어야 한다)

`params.yaml` 에서 `dry_run: false` 로 바꾸거나:

```bash
ros2 run mini_pjt_control mission_manager_node --ros-args --params-file ~/mini_pjt_ws/install/mini_pjt_bringup/share/mini_pjt_bringup/config/params.yaml -p dry_run:=false
```

> **실기 실행 전 체크리스트**
> - [ ] `initial_pose` / `goal_pose` 를 실측값으로 채웠는가
> - [ ] localization + nav2 가 떠 있는가 (`/robot8/amcl_pose` 확인)
> - [ ] 로봇이 독 위에 있는가 (`ros2 topic echo /robot8/dock_status --once`)
> - [ ] 로봇 주변에 사람이 없는가 — **트리거가 들어오면 즉시 언도킹하고 주행한다**

---

## 6. 상태머신 요약

```
IDLE ──(/webcam/trigger == True)──> UNDOCK
                                      │  undock → setInitialPose → waitUntilNav2Active
                                      │  → AMCL 수렴 대기
                                      ▼
                                     NAV ──(실패)──> 재시도 nav_retry 회 ──> FAILED
                                      │ (성공)
                                      ▼
                                  APPROACH
                                      │  cancelTask() → 취소 확인 → /approach/enable=True
                                      │  (/approach/status 의 arrived=True 대기)
                                      ▼
                                    DONE ──> cmd_vel 0, use_dock 이면 dock 복귀
```

### AMCL 수렴 판정

`/robot8/amcl_pose` 의 공분산(6×6 row-major)을 본다.

| 인덱스 | 의미 | 기본 임계 |
|---|---|---|
| `cov[0]` | x 분산 | ≤ 0.05 m² |
| `cov[7]` | y 분산 | ≤ 0.05 m² |
| `cov[35]` | yaw 분산 | ≤ 0.06 rad² |

초기 pose 를 막 뿌린 직후에는 파티클이 퍼져 분산이 크다.
**연속 `amcl_required_hits`(기본 3) 회** 임계 이하일 때만 수렴으로 인정한다.
한 프레임 우연히 낮게 나오는 경우를 걸러내기 위함이다.

수렴이 안 되면 `UNDOCK` 단계에서 `FAILED` 로 떨어진다. 그 경우:
- RViz2 에서 `2D Pose Estimate` 로 초기 위치를 다시 정확히 찍는다
- `initial_pose` 파라미터 값이 실제 독 위치와 맞는지 확인한다
- 로봇을 조금 움직여 스캔 정합이 일어나게 한다 (제자리에 있으면 파티클이 안 줄어든다)

---

## 7. 자주 겪는 문제

| 증상 | 원인 / 조치 |
|---|---|
| `ros2 topic list` 에 로봇 토픽이 안 보임 | 비대화형 셸이라 `ROS_SUPER_CLIENT=False`. 실제 터미널에서 실행하거나 `export ROS_SUPER_CLIENT=True` |
| 토픽은 보이는데 데이터가 안 옴 | QoS 불일치. `ros2 topic info <토픽> -v` 로 발행/구독 Reliability 비교. **BEST_EFFORT 발행 + RELIABLE 구독은 절대 안 붙는다** |
| `waitUntilNav2Active()` 에서 멈춤 | Nav2 가 안 떠 있다. `nav2.launch.py` 확인 |
| AMCL 수렴 실패 | 6절 참고 |
| 주행 중 로봇이 떨림 | Nav2 와 수동 cmd_vel 동시 발행. `ros2 topic info /robot8/cmd_vel -v` 로 Publisher count 확인 |
| `ros2 topic hz` 첫 줄에 `does not appear to be published yet` | Discovery Server 환경에서 첫 연결에 수 초 걸린다. 정상 |
