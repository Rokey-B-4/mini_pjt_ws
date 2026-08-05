// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from mini_pjt_interfaces:msg/RobotState.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_H_
#define MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_H_

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
// Member 'state'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/RobotState in the package mini_pjt_interfaces.
/**
  * 미션 상태머신 / 접근 제어 노드가 발행하는 로봇 상태
 */
typedef struct mini_pjt_interfaces__msg__RobotState
{
  std_msgs__msg__Header header;
  /// 상태 문자열
  ///   INIT, READY, UNDOCKING, NAVIGATING, ARRIVED,
  ///   SEARCHING, APPROACHING, REACHED, DOCKING, DONE, FAILED, ABORTED
  rosidl_runtime_c__String state;
  /// 목표(rc_car)까지의 거리. 미측정 시 -1.0
  float target_distance;
  /// 목표 거리 임계값(기본 0.3m) 이내 도달 여부
  bool arrived;
} mini_pjt_interfaces__msg__RobotState;

// Struct for a sequence of mini_pjt_interfaces__msg__RobotState.
typedef struct mini_pjt_interfaces__msg__RobotState__Sequence
{
  mini_pjt_interfaces__msg__RobotState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} mini_pjt_interfaces__msg__RobotState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_H_
