// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from mini_pjt_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_
#define MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Detection in the package mini_pjt_interfaces.
/**
  * 단일 객체 검출 결과 (웹캠 / 온보드 공용)
 */
typedef struct mini_pjt_interfaces__msg__Detection
{
  /// 클래스 이름 (예: "car", "dummy")
  rosidl_runtime_c__String class_name;
  /// 검출 신뢰도 0.0 ~ 1.0
  float confidence;
  /// bbox 중심 픽셀 좌표
  int32_t center_x;
  int32_t center_y;
  /// bbox 픽셀 좌표 [x1, y1, x2, y2]
  int32_t bbox[4];
} mini_pjt_interfaces__msg__Detection;

// Struct for a sequence of mini_pjt_interfaces__msg__Detection.
typedef struct mini_pjt_interfaces__msg__Detection__Sequence
{
  mini_pjt_interfaces__msg__Detection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mini_pjt_interfaces__msg__Detection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__STRUCT_H_
