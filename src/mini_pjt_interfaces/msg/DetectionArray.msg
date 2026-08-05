# 한 프레임에서 나온 검출 결과 묶음
# header.stamp 은 추론에 사용한 원본 이미지의 타임스탬프를 그대로 넣는다.
# header.frame_id 는 카메라 프레임 (예: "webcam", "oakd_rgb_camera_optical_frame")

std_msgs/Header header
Detection[] detections
