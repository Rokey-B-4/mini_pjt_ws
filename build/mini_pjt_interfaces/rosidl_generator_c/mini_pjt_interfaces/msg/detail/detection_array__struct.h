// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from mini_pjt_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
#define MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'detections'
#include "mini_pjt_interfaces/msg/detail/detection__struct.h"

/// Struct defined in msg/DetectionArray in the package mini_pjt_interfaces.
/**
  * 한 프레임에서 나온 검출 결과 묶음
  * header.stamp 은 추론에 사용한 원본 이미지의 타임스탬프를 그대로 넣는다.
  * header.frame_id 는 카메라 프레임 (예: "webcam", "oakd_rgb_camera_optical_frame")
 */
typedef struct mini_pjt_interfaces__msg__DetectionArray
{
  std_msgs__msg__Header header;
  mini_pjt_interfaces__msg__Detection__Sequence detections;
} mini_pjt_interfaces__msg__DetectionArray;

// Struct for a sequence of mini_pjt_interfaces__msg__DetectionArray.
typedef struct mini_pjt_interfaces__msg__DetectionArray__Sequence
{
  mini_pjt_interfaces__msg__DetectionArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mini_pjt_interfaces__msg__DetectionArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
