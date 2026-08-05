#!/usr/bin/env bash
# ============================================================
#  mini_pjt 환경 점검 스크립트
#
#  사용법:
#     ./check_env.sh              # 기본 네임스페이스 robot8
#     ./check_env.sh robot1       # 다른 네임스페이스로 점검
#     TOPIC_WAIT=10 ./check_env.sh
#
#  주의: colcon build 결과를 보려면 실행 전에 워크스페이스를 source 해두는 것이 좋다.
# ============================================================

NS="${1:-robot8}"
NS="/${NS#/}"                       # 앞에 / 강제
TOPIC_WAIT="${TOPIC_WAIT:-5}"       # ros2 topic list 타임아웃(초)

RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; CYAN=$'\e[36m'; BOLD=$'\e[1m'; RESET=$'\e[0m'

PASS=0
FAIL=0
WARN=0

ok()   { echo "  ${GREEN}[ OK ]${RESET} $1"; PASS=$((PASS+1)); }
bad()  { echo "  ${RED}[FAIL]${RESET} $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ${YELLOW}[WARN]${RESET} $1"; WARN=$((WARN+1)); }
info() { echo "         $1"; }
head_() { echo; echo "${BOLD}${CYAN}== $1 ==${RESET}"; }

# ------------------------------------------------------------
head_ "1. ROS 환경변수"
# ------------------------------------------------------------
echo "  ROS_DISTRO           = ${ROS_DISTRO:-<unset>}"
echo "  ROS_DOMAIN_ID        = ${ROS_DOMAIN_ID:-<unset>}"
echo "  RMW_IMPLEMENTATION   = ${RMW_IMPLEMENTATION:-<unset>}"
echo "  ROS_DISCOVERY_SERVER = ${ROS_DISCOVERY_SERVER:-<unset>}"
echo "  ROS_SUPER_CLIENT     = ${ROS_SUPER_CLIENT:-<unset>}"
echo "  ROS_LOCALHOST_ONLY   = ${ROS_LOCALHOST_ONLY:-<unset>}"
echo "  target namespace     = ${NS}"
echo

if [ "$ROS_DISTRO" = "humble" ]; then
  ok "ROS_DISTRO=humble"
else
  bad "ROS_DISTRO 가 humble 이 아님 (${ROS_DISTRO:-<unset>}) — /opt/ros/humble/setup.bash 를 source 했는지 확인"
fi

if [ -z "$ROS_DOMAIN_ID" ]; then
  bad "ROS_DOMAIN_ID 미설정 — 기본 0 으로 동작하므로 로봇(8)과 통신 불가"
elif [ "$ROS_DOMAIN_ID" = "8" ]; then
  ok "ROS_DOMAIN_ID=8 (프로젝트 기준값)"
else
  bad "ROS_DOMAIN_ID=${ROS_DOMAIN_ID} — 로봇과 동일한 8 이어야 함"
fi

if [ "$RMW_IMPLEMENTATION" = "rmw_fastrtps_cpp" ]; then
  ok "RMW_IMPLEMENTATION=rmw_fastrtps_cpp"
elif [ -z "$RMW_IMPLEMENTATION" ]; then
  warn "RMW_IMPLEMENTATION 미설정 — 기본값 사용. 로봇과 다르면 토픽이 전혀 안 보인다"
else
  bad "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION} — 로봇과 반드시 동일해야 함(rmw_fastrtps_cpp)"
fi

if [ "$ROS_LOCALHOST_ONLY" = "1" ]; then
  bad "ROS_LOCALHOST_ONLY=1 — 로컬 전용이라 로봇이 절대 안 보인다. 0 으로 바꿀 것"
fi

# /etc/turtlebot4_discovery/setup.bash 는 [ -t 0 ] 로 TTY 를 검사해서
# 비대화형 셸(스크립트/에디터/런치)에서는 ROS_SUPER_CLIENT=False 가 된다.
# False 면 Discovery Server 가 알려주는 것만 보여서 토픽이 부분적으로만 보일 수 있다.
if [ "$ROS_SUPER_CLIENT" = "False" ]; then
  warn "ROS_SUPER_CLIENT=False — 비대화형 셸이라 discovery 가 제한된다."
  info "  실제 터미널에서 직접 실행하거나, export ROS_SUPER_CLIENT=True 후 재시도할 것"
elif [ "$ROS_SUPER_CLIENT" = "True" ]; then
  ok "ROS_SUPER_CLIENT=True"
fi

# Discovery Server 사용 시 서버 도달성 확인
if [ -n "$ROS_DISCOVERY_SERVER" ]; then
  DS_HOST=$(echo "$ROS_DISCOVERY_SERVER" | tr ';' '\n' | grep -m1 ':' | cut -d: -f1)
  DS_PORT=$(echo "$ROS_DISCOVERY_SERVER" | tr ';' '\n' | grep -m1 ':' | cut -d: -f2)
  if [ -n "$DS_HOST" ]; then
    info "Discovery Server: ${DS_HOST}:${DS_PORT}"
    if ping -c1 -W2 "$DS_HOST" >/dev/null 2>&1; then
      ok "Discovery Server 호스트 ping 응답 (${DS_HOST})"
    else
      bad "Discovery Server 호스트 ping 실패 (${DS_HOST}) — 네트워크/로봇 전원 확인"
    fi
    if command -v nc >/dev/null 2>&1; then
      if nc -z -w2 "$DS_HOST" "$DS_PORT" >/dev/null 2>&1; then
        ok "Discovery Server 포트 열림 (${DS_HOST}:${DS_PORT})"
      else
        warn "Discovery Server 포트 ${DS_PORT} 응답 없음 (UDP 라 nc 판정이 부정확할 수 있음)"
      fi
    fi
  fi
fi

# ------------------------------------------------------------
head_ "2. ros2 daemon 상태"
# ------------------------------------------------------------
if ! command -v ros2 >/dev/null 2>&1; then
  bad "ros2 명령을 찾을 수 없음 — setup.bash 를 source 하지 않았다"
  echo
  echo "${BOLD}중단: ROS2 환경이 없어 이후 점검을 진행할 수 없습니다.${RESET}"
  exit 1
fi

DAEMON_OUT=$(ros2 daemon status 2>&1)
echo "  ${DAEMON_OUT}"
if echo "$DAEMON_OUT" | grep -qi "not running"; then
  warn "ros2 daemon 미실행 — 지금 기동한다"
  ros2 daemon start >/dev/null 2>&1
  sleep 1
elif echo "$DAEMON_OUT" | grep -qi "running"; then
  ok "ros2 daemon 실행 중"
else
  warn "ros2 daemon 상태 판정 불가: ${DAEMON_OUT}"
fi
info "토픽이 이상하게 안 보이면: ros2 daemon stop && ros2 daemon start"

# ------------------------------------------------------------
head_ "3. 토픽 수집 (timeout ${TOPIC_WAIT}s)"
# ------------------------------------------------------------
TOPICS=$(timeout "${TOPIC_WAIT}" ros2 topic list 2>/dev/null)
TOPIC_COUNT=$(echo "$TOPICS" | grep -c '^/' )

if [ -z "$TOPICS" ]; then
  bad "토픽이 하나도 안 보임 — 로봇 미연결이거나 DOMAIN_ID/RMW 불일치"
  TOPIC_COUNT=0
else
  info "총 ${TOPIC_COUNT} 개 토픽 발견"
  if [ "$TOPIC_COUNT" -le 2 ]; then
    warn "토픽이 ${TOPIC_COUNT}개뿐 (/parameter_events, /rosout 만 보이는 상태) — 로봇이 안 보인다"
  fi
fi

check_topic() {
  # $1 = 토픽 경로, $2 = 설명
  if echo "$TOPICS" | grep -qx "$1"; then
    ok "$1  ($2)"
    return 0
  else
    bad "$1  ($2) — 없음"
    return 1
  fi
}

# ------------------------------------------------------------
head_ "4. 필수 토픽 존재 여부 (namespace: ${NS})"
# ------------------------------------------------------------
check_topic "${NS}/cmd_vel"     "주행 속도 명령"
check_topic "${NS}/odom"        "오도메트리"
check_topic "${NS}/dock_status" "도킹 상태"

echo
echo "  ${BOLD}-- OAK-D 카메라 --${RESET}"
check_topic "${NS}/oakd/rgb/image_raw/compressed" "RGB (compressed)"
check_topic "${NS}/oakd/stereo/image_raw"         "Depth"
check_topic "${NS}/oakd/rgb/camera_info"          "카메라 내부 파라미터"

OAKD_ALL=$(echo "$TOPICS" | grep -c "^${NS}/oakd/")
info "${NS}/oakd/* 토픽 총 ${OAKD_ALL} 개"
if [ "$OAKD_ALL" -eq 0 ]; then
  bad "${NS}/oakd/* 토픽이 전혀 없음"
  echo
  echo "  ${YELLOW}원인 후보:${RESET}"
  echo "     - depthai lazy publisher: 구독자가 붙기 전에는 토픽을 광고하지 않는다"
  echo "       확인:  ros2 param get ${NS}/oakd rgb.i_enable_lazy_publisher"
  echo "       해제:  ros2 param set ${NS}/oakd rgb.i_enable_lazy_publisher false"
  echo "              ros2 param set ${NS}/oakd stereo.i_enable_lazy_publisher false"
  echo "     - 네임스페이스 불일치 / 카메라 미기동 (ros2 node list 에 ${NS}/oakd 있는지 확인)"
  echo
  info "실제로 보이는 네임스페이스 후보:"
  echo "$TOPICS" | grep '^/' | cut -d/ -f2 | sort -u | grep -v -E '^(parameter_events|rosout|tf|tf_static|clock|diagnostics)$' \
    | sed 's/^/           \//' | head -10
fi

echo
echo "  ${BOLD}-- Nav2 관련 --${RESET}"
for t in "${NS}/map" "${NS}/amcl_pose" "${NS}/initialpose"; do
  if echo "$TOPICS" | grep -qx "$t"; then
    ok "$t"
  else
    warn "$t — 없음 (Nav2 미기동 상태일 수 있음)"
  fi
done

# ------------------------------------------------------------
head_ "5. 노드 목록"
# ------------------------------------------------------------
NODES=$(timeout "${TOPIC_WAIT}" ros2 node list 2>/dev/null)
NODE_COUNT=$(echo "$NODES" | grep -c '^/')
if [ -z "$NODES" ]; then
  bad "노드가 하나도 안 보임"
  NODE_COUNT=0
else
  info "총 ${NODE_COUNT} 개 노드"
  echo "$NODES" | sed 's/^/           /' | head -25
  [ "$NODE_COUNT" -gt 25 ] && info "... (이하 생략)"
fi

ROBOT_NODES=$(echo "$NODES" | grep -c "^${NS}/")
if [ "$ROBOT_NODES" -gt 0 ]; then
  ok "${NS} 네임스페이스 노드 ${ROBOT_NODES} 개 발견 — 로봇과 통신 성립"
else
  bad "${NS} 네임스페이스 노드 없음 — 로봇이 보이지 않는다"
fi

# ------------------------------------------------------------
head_ "6. 양방향 통신 판정 (원격 PC <-> 터틀봇4)"
# ------------------------------------------------------------
if [ "$ROBOT_NODES" -gt 0 ]; then
  ok "로봇 -> PC 방향: 로봇 노드/토픽이 PC 에서 보임"

  # 실제 데이터가 흐르는지 확인 (토픽 존재 != 데이터 발행)
  if echo "$TOPICS" | grep -qx "${NS}/odom"; then
    # Discovery Server 환경에서는 첫 연결 수립에 10초 이상 걸리는 경우가 있다.
    HZ=$(timeout 15 ros2 topic hz "${NS}/odom" 2>/dev/null | grep -m1 "average rate")
    if [ -n "$HZ" ]; then
      ok "${NS}/odom 데이터 수신 확인 (${HZ})"
    else
      bad "${NS}/odom 토픽은 있으나 15초 내 데이터 없음 — QoS 불일치 또는 로봇 정지 상태"
    fi
  fi

  # PC -> 로봇 방향: PC 가 발행한 토픽을 로봇 쪽 노드가 구독 중인지 확인
  if echo "$TOPICS" | grep -qx "${NS}/cmd_vel"; then
    SUBS=$(timeout 5 ros2 topic info "${NS}/cmd_vel" 2>/dev/null | grep -i "Subscription count" | grep -oE '[0-9]+')
    if [ -n "$SUBS" ] && [ "$SUBS" -gt 0 ]; then
      ok "PC -> 로봇 방향: ${NS}/cmd_vel 구독자 ${SUBS} 개 (로봇이 명령 수신 대기 중)"
    else
      bad "${NS}/cmd_vel 구독자 0 — PC 에서 보낸 속도 명령이 로봇에 도달하지 않는다"
    fi
  fi
else
  bad "로봇 -> PC 방향 통신 실패"
  echo
  echo "  ${YELLOW}점검 순서:${RESET}"
  echo "     1) 로봇 전원 / 네트워크 연결 확인"
  echo "     2) PC 와 로봇의 ROS_DOMAIN_ID 가 모두 8 인지"
  echo "     3) PC 와 로봇의 RMW_IMPLEMENTATION 이 모두 rmw_fastrtps_cpp 인지"
  echo "     4) source /etc/turtlebot4_discovery/setup.bash 했는지"
  echo "     5) ros2 daemon stop && ros2 daemon start 후 재시도"
fi

# ------------------------------------------------------------
head_ "7. 로컬 의존성 (로봇 없이도 확인 가능)"
# ------------------------------------------------------------
while IFS='|' read -r status rest; do
  case "$status" in
    OK) ok "$rest" ;;
    NG) bad "$rest" ;;
  esac
done < <(python3 - <<'PY' 2>/dev/null
import importlib
mods = [("ultralytics", "YOLO 추론"),
        ("torch", "PyTorch"),
        ("cv2", "OpenCV"),
        ("cv_bridge", "ROS<->OpenCV 변환"),
        ("message_filters", "RGB/Depth 동기화")]
for m, desc in mods:
    try:
        importlib.import_module(m)
        print(f"OK|{m} ({desc})")
    except Exception as e:
        print(f"NG|{m} ({desc}) - {type(e).__name__}")
try:
    import torch
    print(f"{'OK' if torch.cuda.is_available() else 'NG'}|CUDA "
          f"({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'GPU 사용 불가'})")
except Exception:
    print("NG|CUDA (torch import 실패)")
PY
)

# 커스텀 메시지 빌드 확인
if python3 -c "import mini_pjt_interfaces.msg" >/dev/null 2>&1; then
  ok "mini_pjt_interfaces 메시지 import 가능 (빌드 + source 완료)"
else
  warn "mini_pjt_interfaces import 불가 — colcon build 후 install/setup.bash 를 source 할 것"
fi

# 웹캠
WEBCAM_FOUND=0
for dev in /dev/video*; do
  [ -e "$dev" ] && WEBCAM_FOUND=$((WEBCAM_FOUND+1))
done
if [ "$WEBCAM_FOUND" -gt 0 ]; then
  ok "/dev/video* 장치 ${WEBCAM_FOUND} 개 발견"
  ls /dev/video* 2>/dev/null | sed 's/^/           /'
else
  bad "/dev/video* 없음 — USB 웹캠 미연결"
fi

# ------------------------------------------------------------
head_ "요약"
# ------------------------------------------------------------
echo "  ${GREEN}OK  : ${PASS}${RESET}"
echo "  ${YELLOW}WARN: ${WARN}${RESET}"
echo "  ${RED}FAIL: ${FAIL}${RESET}"
echo
if [ "$FAIL" -eq 0 ]; then
  echo "  ${GREEN}${BOLD}==> 전체 OK${RESET}"
  exit 0
elif [ "$ROBOT_NODES" -eq 0 ] 2>/dev/null; then
  echo "  ${YELLOW}${BOLD}==> 로봇 미연결 상태. 웹캠 단독 개발은 진행 가능.${RESET}"
  exit 2
else
  echo "  ${RED}${BOLD}==> FAIL 항목 확인 필요${RESET}"
  exit 1
fi
