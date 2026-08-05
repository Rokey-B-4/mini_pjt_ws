// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from mini_pjt_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "mini_pjt_interfaces/msg/detail/detection_array__rosidl_typesupport_introspection_c.h"
#include "mini_pjt_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "mini_pjt_interfaces/msg/detail/detection_array__functions.h"
#include "mini_pjt_interfaces/msg/detail/detection_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `detections`
#include "mini_pjt_interfaces/msg/detection.h"
// Member `detections`
#include "mini_pjt_interfaces/msg/detail/detection__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  mini_pjt_interfaces__msg__DetectionArray__init(message_memory);
}

void mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_fini_function(void * message_memory)
{
  mini_pjt_interfaces__msg__DetectionArray__fini(message_memory);
}

size_t mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__size_function__DetectionArray__detections(
  const void * untyped_member)
{
  const mini_pjt_interfaces__msg__Detection__Sequence * member =
    (const mini_pjt_interfaces__msg__Detection__Sequence *)(untyped_member);
  return member->size;
}

const void * mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_const_function__DetectionArray__detections(
  const void * untyped_member, size_t index)
{
  const mini_pjt_interfaces__msg__Detection__Sequence * member =
    (const mini_pjt_interfaces__msg__Detection__Sequence *)(untyped_member);
  return &member->data[index];
}

void * mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_function__DetectionArray__detections(
  void * untyped_member, size_t index)
{
  mini_pjt_interfaces__msg__Detection__Sequence * member =
    (mini_pjt_interfaces__msg__Detection__Sequence *)(untyped_member);
  return &member->data[index];
}

void mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__fetch_function__DetectionArray__detections(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const mini_pjt_interfaces__msg__Detection * item =
    ((const mini_pjt_interfaces__msg__Detection *)
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_const_function__DetectionArray__detections(untyped_member, index));
  mini_pjt_interfaces__msg__Detection * value =
    (mini_pjt_interfaces__msg__Detection *)(untyped_value);
  *value = *item;
}

void mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__assign_function__DetectionArray__detections(
  void * untyped_member, size_t index, const void * untyped_value)
{
  mini_pjt_interfaces__msg__Detection * item =
    ((mini_pjt_interfaces__msg__Detection *)
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_function__DetectionArray__detections(untyped_member, index));
  const mini_pjt_interfaces__msg__Detection * value =
    (const mini_pjt_interfaces__msg__Detection *)(untyped_value);
  *item = *value;
}

bool mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__resize_function__DetectionArray__detections(
  void * untyped_member, size_t size)
{
  mini_pjt_interfaces__msg__Detection__Sequence * member =
    (mini_pjt_interfaces__msg__Detection__Sequence *)(untyped_member);
  mini_pjt_interfaces__msg__Detection__Sequence__fini(member);
  return mini_pjt_interfaces__msg__Detection__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__DetectionArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "detections",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__DetectionArray, detections),  // bytes offset in struct
    NULL,  // default value
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__size_function__DetectionArray__detections,  // size() function pointer
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_const_function__DetectionArray__detections,  // get_const(index) function pointer
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__get_function__DetectionArray__detections,  // get(index) function pointer
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__fetch_function__DetectionArray__detections,  // fetch(index, &value) function pointer
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__assign_function__DetectionArray__detections,  // assign(index, value) function pointer
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__resize_function__DetectionArray__detections  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_members = {
  "mini_pjt_interfaces__msg",  // message namespace
  "DetectionArray",  // message name
  2,  // number of fields
  sizeof(mini_pjt_interfaces__msg__DetectionArray),
  mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_member_array,  // message members
  mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_init_function,  // function to initialize message memory (memory has to be allocated)
  mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_type_support_handle = {
  0,
  &mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_mini_pjt_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mini_pjt_interfaces, msg, DetectionArray)() {
  mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mini_pjt_interfaces, msg, Detection)();
  if (!mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_type_support_handle.typesupport_identifier) {
    mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &mini_pjt_interfaces__msg__DetectionArray__rosidl_typesupport_introspection_c__DetectionArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
