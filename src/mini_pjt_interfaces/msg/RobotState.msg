# 미션 상태머신 / 접근 제어 노드가 발행하는 로봇 상태

std_msgs/Header header

# 상태 문자열
#   INIT, READY, UNDOCKING, NAVIGATING, ARRIVED,
#   SEARCHING, APPROACHING, REACHED, DOCKING, DONE, FAILED, ABORTED
string state

# 목표(rc_car)까지의 거리 [m]. 미측정 시 -1.0
float32 target_distance

# 목표 거리 임계값(기본 0.3m) 이내 도달 여부
bool arrived
