// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from mini_pjt_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "mini_pjt_interfaces/msg/detail/detection__rosidl_typesupport_introspection_c.h"
#include "mini_pjt_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "mini_pjt_interfaces/msg/detail/detection__functions.h"
#include "mini_pjt_interfaces/msg/detail/detection__struct.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  mini_pjt_interfaces__msg__Detection__init(message_memory);
}

void mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_fini_function(void * message_memory)
{
  mini_pjt_interfaces__msg__Detection__fini(message_memory);
}

size_t mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__size_function__Detection__bbox(
  const void * untyped_member)
{
  (void)untyped_member;
  return 4;
}

const void * mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_const_function__Detection__bbox(
  const void * untyped_member, size_t index)
{
  const int32_t * member =
    (const int32_t *)(untyped_member);
  return &member[index];
}

void * mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_function__Detection__bbox(
  void * untyped_member, size_t index)
{
  int32_t * member =
    (int32_t *)(untyped_member);
  return &member[index];
}

void mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__fetch_function__Detection__bbox(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const int32_t * item =
    ((const int32_t *)
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_const_function__Detection__bbox(untyped_member, index));
  int32_t * value =
    (int32_t *)(untyped_value);
  *value = *item;
}

void mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__assign_function__Detection__bbox(
  void * untyped_member, size_t index, const void * untyped_value)
{
  int32_t * item =
    ((int32_t *)
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_function__Detection__bbox(untyped_member, index));
  const int32_t * value =
    (const int32_t *)(untyped_value);
  *item = *value;
}

static rosidl_typesupport_introspection_c__MessageMember mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_member_array[5] = {
  {
    "class_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__Detection, class_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "confidence",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__Detection, confidence),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "center_x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__Detection, center_x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "center_y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__Detection, center_y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "bbox",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    4,  // array size
    false,  // is upper bound
    offsetof(mini_pjt_interfaces__msg__Detection, bbox),  // bytes offset in struct
    NULL,  // default value
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__size_function__Detection__bbox,  // size() function pointer
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_const_function__Detection__bbox,  // get_const(index) function pointer
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__get_function__Detection__bbox,  // get(index) function pointer
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__fetch_function__Detection__bbox,  // fetch(index, &value) function pointer
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__assign_function__Detection__bbox,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_members = {
  "mini_pjt_interfaces__msg",  // message namespace
  "Detection",  // message name
  5,  // number of fields
  sizeof(mini_pjt_interfaces__msg__Detection),
  mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_member_array,  // message members
  mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_init_function,  // function to initialize message memory (memory has to be allocated)
  mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_type_support_handle = {
  0,
  &mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_mini_pjt_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, mini_pjt_interfaces, msg, Detection)() {
  if (!mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_type_support_handle.typesupport_identifier) {
    mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &mini_pjt_interfaces__msg__Detection__rosidl_typesupport_introspection_c__Detection_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
