# 단일 객체 검출 결과 (웹캠 / 온보드 공용)

# 클래스 이름 (예: "car", "dummy")
string class_name

# 검출 신뢰도 0.0 ~ 1.0
float32 confidence

# bbox 중심 픽셀 좌표
int32 center_x
int32 center_y

# bbox 픽셀 좌표 [x1, y1, x2, y2]
int32[4] bbox
