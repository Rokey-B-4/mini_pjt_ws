# README_vision — OAK-D 동기화 / 좌표 정합 / 검증 절차

Phase 3 산출물인 `oakd_probe` 와 `robot_detector_node` 의 사용법과 검증 절차.

---

## 0. 공통 준비

```bash
source /opt/ros/humble/setup.bash && source ~/turtlebot4_ws/install/setup.bash && source /etc/turtlebot4_discovery/setup.bash && source ~/mini_pjt_ws/install/setup.bash
```

---

## 1. oakd_probe — 진단 스크립트

```bash
ros2 run mini_pjt_vision oakd_probe --ns /robot8 --samples 100
```

옵션:

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--ns` | `/robot8` | 로봇 네임스페이스 |
| `--samples` | `100` | 타임스탬프 차이 샘플 수 |
| `--warmup` | `8.0` | 토픽 수집 시간(초) |
| `--timeout` | `60.0` | 동기화 측정 제한(초) |

출력 3부:
1. `/oakd/` 하위 토픽 — 타입, 주기, 해상도, encoding, frame_id
2. RGB / Depth `camera_info` 나란히 비교 (K, D, 해상도, distortion_model) + **해상도비 vs 초점거리비**
3. RGB↔Depth `header.stamp` 차이 분포 (평균/최대/표준편차) + **권장 slop**

3번의 권장 slop 을 `params.yaml` 의 `sync_slop_sec` 에 넣으면 된다.

### 토픽이 하나도 안 잡힐 때

스크립트가 이미 blind subscribe 를 시도하므로, 그래도 0 이면 카메라 쪽 문제다.
아래 순서로 확인한다:

```bash
ros2 node info /robot8/oakd
```

`Publishers:` 에 `/parameter_events`, `/rosout` **만** 있으면 DepthAI 파이프라인이
아예 안 뜬 것이다 (lazy publisher 문제가 아니다). 로봇에서 카메라를 재시작해야 한다:

```bash
ssh ubuntu@192.168.101.108
```
```bash
sudo systemctl restart turtlebot4.service
```

파이프라인은 떴는데 스트림만 안 나오면 그때가 lazy publisher 문제다:

```bash
ros2 param set /robot8/oakd rgb.i_enable_lazy_publisher false
```
```bash
ros2 param set /robot8/oakd stereo.i_enable_lazy_publisher false
```

> 이 파라미터는 depthai 드라이버가 **파이프라인 생성 시점에만** 읽는다.
> 런타임에 바꿔도 이미 만들어진 파이프라인에는 반영되지 않으므로,
> 영구 적용하려면 로봇의 `oakd` 설정 yaml 을 고치고 재시작해야 한다.

---

## 2. robot_detector_node

```bash
cd ~/mini_pjt_ws && ros2 run mini_pjt_vision robot_detector_node --ros-args --params-file install/mini_pjt_bringup/share/mini_pjt_bringup/config/params.yaml
```

발행:

| 토픽 | 타입 |
|---|---|
| `/robot/detections` | `mini_pjt_interfaces/DetectionArray` |
| `/robot/target_distance` | `std_msgs/Float32` (없으면 `-1.0`) |
| `/robot/annotated` | `sensor_msgs/Image` (base) |
| `/robot/annotated/compressed` | `sensor_msgs/CompressedImage` |

영상 확인 — **base 토픽**을 준다:

```bash
ros2 run rqt_image_view rqt_image_view /robot/annotated
```

### 실행 중 로그로 확인할 것

5초마다 이런 줄이 나온다:

```
[동기화] rgb  10.0 Hz | depth  15.0 Hz | sync   9.8 Hz | 드롭   2.0% (slop=0.050s)
```

- `rgb` 또는 `depth` 가 `0.0 Hz` → 카메라가 안 나온다 (1절 참고)
- `드롭` 이 50% 넘으면 경고가 뜬다 → `sync_slop_sec` 를 키운다
- `sync` 가 `min(rgb, depth)` 에 가까울수록 좋다

---

## 3. RGB ↔ Depth 좌표 정합

OAK-D 의 RGB(preview) 와 Depth(stereo) 는 **해상도도 FOV 도 다르다.**
RGB 에서 찾은 bbox 중심 픽셀을 그대로 depth 이미지에 쓰면 엉뚱한 곳의 거리를 읽는다.

### 방식 1 — `projection_mode: "intrinsic"` (기본, 정식)

```
u_rgb  ──K_rgb⁻¹──>  정규화 좌표          ──K_depth──>  u_depth
                     x = (u - cx_rgb)/fx_rgb           u_d = fx_d·x + cx_d
                     y = (v - cy_rgb)/fy_rgb           v_d = fy_d·y + cy_d
```

두 카메라 사이 extrinsic(R, t) 이 `camera_info` 에 없으므로 **근사 동축**을 가정한다.
베이스라인만큼의 시차는 남지만, 수 m 거리에서는 수 픽셀 수준이라 무시할 만하다.

`camera_info` 의 해상도와 실제 수신 이미지 해상도가 다르면(리사이즈된 preview 등)
K 를 그 비율로 보정한 뒤 계산한다.

### 방식 2 — `projection_mode: "scale"` (fallback)

```
u_d = u_rgb × (W_depth / W_rgb)
v_d = v_rgb × (H_depth / H_rgb)
```

FOV 가 같을 때만 맞다. 다르면 **화면 중심에서 멀어질수록 오차가 커진다.**

### 두 방식 비교하기

`log_projection_compare: true` (기본) 로 두면 매 검출마다 이런 로그가 나온다:

```
[정합비교] rgb(320,240) -> intrinsic (208.3,156.2) d=1.234 m | other (213.3,160.0) d=1.251 m | 픽셀차 (5.0,3.8)
```

- **픽셀차가 작고 거리도 비슷** → 두 카메라 FOV 가 비슷하다. 어느 쪽을 써도 된다.
- **픽셀차가 크다** → 반드시 `intrinsic` 을 써야 한다.
- **한쪽 거리가 `None`** → 그 좌표가 depth 이미지 밖이거나 유효 depth 가 없다.

`oakd_probe` 의 2절 출력에서도 미리 짐작할 수 있다:

```
해상도 비  : x 0.5333   y 0.5333
초점거리 비: fx 0.5341   fy 0.5341
```

두 비율이 비슷하면 스케일 방식도 쓸 만하고, 크게 다르면 `intrinsic` 이 필수다.

### 정합이 맞는지 눈으로 확인하는 법

RC카를 화면 **중앙**에 두었을 때와 **가장자리**에 두었을 때 거리값을 비교한다.

```bash
ros2 topic echo /robot/target_distance
```

같은 거리에 있는데 가장자리에서만 값이 튀거나 `-1.0` 이 나오면 정합이 틀린 것이다.
`projection_mode` 를 바꿔가며 다시 확인한다.

---

## 4. depth encoding 처리

런타임에 `depth_msg.encoding` 을 보고 분기한다.

| encoding | 단위 | 처리 |
|---|---|---|
| `16UC1` | mm | `/ 1000.0` |
| `mono16` | mm | `/ 1000.0` |
| `32FC1` | m | 그대로 |
| 그 외 | ? | **에러 로그 후 프레임 폐기** |

예상 밖 encoding 이면 이런 로그가 한 번 뜬다:

```
[ERROR] 예상 밖의 depth encoding 'XXXX' 입니다. 지원: 16UC1(mm), mono16(mm), 32FC1(m). 이 프레임은 버립니다.
```

실제 encoding 은 `oakd_probe` 1절에서 확인할 수 있다.

---

## 5. 검증 절차 A — 제자리 회전 시 거리 안정성

**목적**: 좌표 정합과 depth 샘플링이 제대로 되면, 로봇이 제자리 회전해도
RC카가 화면에 잡혀 있는 동안 거리값이 매끄럽게 변해야 한다. 튀면 정합이 틀렸거나
동기화가 안 맞는 것이다.

### 준비

RC카를 로봇 앞 **1.0 m** 쯤에 고정해 둔다 (줄자로 실측해 둘 것).

터미널 1 — 검출 노드:
```bash
cd ~/mini_pjt_ws && ros2 run mini_pjt_vision robot_detector_node --ros-args --params-file install/mini_pjt_bringup/share/mini_pjt_bringup/config/params.yaml
```

터미널 2 — 거리 기록:
```bash
ros2 topic echo /robot/target_distance --field data > /tmp/dist_rotate.txt
```

터미널 3 — 영상 확인:
```bash
ros2 run rqt_image_view rqt_image_view /robot/annotated
```

터미널 4 — 제자리 저속 회전 (0.3 rad/s):
```bash
ros2 topic pub -r 10 /robot8/cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.3}}"
```

> Nav2 가 떠 있으면 cmd_vel 이 겹친다. 이 테스트 동안에는 Nav2 를 끄거나
> `mission_manager_node` 를 IDLE 로 두고 한다.

RC카가 화면 왼쪽 끝 → 중앙 → 오른쪽 끝을 지나가도록 반 바퀴만 돌린 뒤 `Ctrl+C`.

### 판정

```bash
python3 -c "
import statistics
v=[float(x) for x in open('/tmp/dist_rotate.txt') if x.strip() and float(x)>0]
print(f'샘플 {len(v)}개')
print(f'평균 {statistics.mean(v):.3f} m / 최소 {min(v):.3f} / 최대 {max(v):.3f}')
print(f'표준편차 {statistics.pstdev(v):.3f} m')
d=[abs(v[i+1]-v[i]) for i in range(len(v)-1)]
print(f'프레임간 최대 변화 {max(d):.3f} m')
"
```

| 지표 | 합격 기준 (1 m 기준) | 불합격이면 |
|---|---|---|
| 평균 | 실측값 ±0.05 m | 정합 방식 변경, depth 단위 확인 |
| 표준편차 | < 0.05 m | `depth_patch_size` 를 9~11 로 키움 |
| 프레임간 최대 변화 | < 0.10 m | slop 축소, 정합 방식 변경 |
| `-1.0` 비율 | < 10% | `conf_thres` 낮추거나 정합 확인 |

**전형적인 실패 패턴**

- 화면 가장자리에서만 값이 튄다 → **좌표 정합 오류.** `projection_mode` 를 바꿔본다.
- 회전 속도를 올리면 값이 튄다 → **동기화 문제.** slop 을 줄인다 (6절).
- 값이 항상 1000배 크거나 작다 → **encoding 오판.** 1절에서 encoding 확인.
- 값이 계단처럼 뚝뚝 끊긴다 → depth 유효 픽셀 부족. `depth_patch_size` 를 키운다.

---

## 6. 검증 절차 B — slop 값 비교 (0.01 ~ 0.1)

**목적**: slop 이 너무 작으면 동기화 콜백이 거의 안 불리고, 너무 크면 시간이
안 맞는 RGB/Depth 가 짝지어져 **움직일 때** 거리값이 튄다. 그 절충점을 찾는다.

### 절차

RC카를 1 m 에 고정하고, 각 slop 값마다 **정지 상태 30초** + **회전 상태 30초**를 측정한다.

```bash
for S in 0.01 0.02 0.03 0.05 0.08 0.10; do
  echo "=== slop=$S ==="
  timeout 40 ros2 run mini_pjt_vision robot_detector_node --ros-args --params-file ~/mini_pjt_ws/install/mini_pjt_bringup/share/mini_pjt_bringup/config/params.yaml -p sync_slop_sec:=$S 2>&1 | grep "동기화" | tail -5
done
```

각 실행에서 나오는 로그를 표로 정리한다:

```
[동기화] rgb  10.0 Hz | depth  15.0 Hz | sync   9.8 Hz | 드롭   2.0% (slop=0.050s)
```

| slop | sync Hz | 드롭률 | 회전 시 거리 표준편차 |
|---|---|---|---|
| 0.01 | ? | ? | ? |
| 0.02 | | | |
| 0.03 | | | |
| 0.05 | | | |
| 0.08 | | | |
| 0.10 | | | |

회전 시 표준편차는 5절 방법으로 각 slop 마다 측정한다.

### 고르는 기준

1. **드롭률이 20% 미만**인 값들 중에서
2. **회전 시 표준편차가 가장 작은** 값을 고른다

드롭률과 안정성이 상충하면 **드롭률을 조금 희생하고 작은 slop** 을 택한다.
프레임을 몇 장 버리는 것보다 틀린 거리값을 내는 쪽이 위험하기 때문이다
(접근 제어가 그 값으로 로봇을 움직인다).

### 이론적 하한

`oakd_probe` 3절이 알려주는 실측 최대 차이보다 slop 이 작으면 동기화가 거의 안 된다.

```
|차이| 평균:    12.30 ms
|차이| 최대:    31.50 ms
>>> 권장 slop: 0.047 s
```

이 경우 `slop < 0.032` 부터 드롭률이 급증한다. 권장값에서 시작해 조금씩 줄여가며
드롭률이 꺾이는 지점을 찾으면 된다.

### RGB fps 가 낮은 점 주의

이 로봇은 `rgb.i_fps = 10.0` (720P) 이다. Depth 는 보통 더 빠르다.
따라서 **동기화 상한은 10 Hz** 이고, 접근 제어 주기(`control_rate_hz: 10.0`)와 같다.
RGB fps 를 올리려면 로봇의 oakd 설정을 바꿔야 한다:

```bash
ros2 param get /robot8/oakd rgb.i_fps
```

---

## 7. 자주 겪는 문제

| 증상 | 원인 / 조치 |
|---|---|
| `rgb 0.0 Hz` 또는 `depth 0.0 Hz` | `ros2 node info /robot8/oakd` 로 퍼블리셔 확인. 없으면 로봇에서 카메라 재시작 |
| 토픽은 보이는데 데이터 0 | QoS. 이미지 구독은 반드시 `SensorDataQoS(best_effort)`. RELIABLE 이면 한 장도 안 온다 |
| 거리가 항상 `-1.0` | 검출은 되는데 depth 가 무효. `depth_min_valid_m` / `depth_max_valid_m` 범위 확인 |
| 거리가 1000배 이상 | encoding 오판. 4절 참고 |
| 화면 가장자리에서만 거리 이상 | 좌표 정합. `log_projection_compare` 로 두 방식 비교 |
| `rqt_image_view` 검은 화면 | base 토픽 `/robot/annotated` 를 줄 것. `/compressed` 를 직접 주면 타입 충돌 |
| 드롭률 90%+ | slop 이 너무 작거나 rgb/depth fps 차이가 큼 |
