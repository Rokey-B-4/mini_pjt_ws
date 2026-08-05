// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from mini_pjt_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice
#include "mini_pjt_interfaces/msg/detail/detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

bool
mini_pjt_interfaces__msg__Detection__init(mini_pjt_interfaces__msg__Detection * msg)
{
  if (!msg) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__init(&msg->class_name)) {
    mini_pjt_interfaces__msg__Detection__fini(msg);
    return false;
  }
  // confidence
  // center_x
  // center_y
  // bbox
  return true;
}

void
mini_pjt_interfaces__msg__Detection__fini(mini_pjt_interfaces__msg__Detection * msg)
{
  if (!msg) {
    return;
  }
  // class_name
  rosidl_runtime_c__String__fini(&msg->class_name);
  // confidence
  // center_x
  // center_y
  // bbox
}

bool
mini_pjt_interfaces__msg__Detection__are_equal(const mini_pjt_interfaces__msg__Detection * lhs, const mini_pjt_interfaces__msg__Detection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->class_name), &(rhs->class_name)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // center_x
  if (lhs->center_x != rhs->center_x) {
    return false;
  }
  // center_y
  if (lhs->center_y != rhs->center_y) {
    return false;
  }
  // bbox
  for (size_t i = 0; i < 4; ++i) {
    if (lhs->bbox[i] != rhs->bbox[i]) {
      return false;
    }
  }
  return true;
}

bool
mini_pjt_interfaces__msg__Detection__copy(
  const mini_pjt_interfaces__msg__Detection * input,
  mini_pjt_interfaces__msg__Detection * output)
{
  if (!input || !output) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__copy(
      &(input->class_name), &(output->class_name)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // center_x
  output->center_x = input->center_x;
  // center_y
  output->center_y = input->center_y;
  // bbox
  for (size_t i = 0; i < 4; ++i) {
    output->bbox[i] = input->bbox[i];
  }
  return true;
}

mini_pjt_interfaces__msg__Detection *
mini_pjt_interfaces__msg__Detection__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mini_pjt_interfaces__msg__Detection * msg = (mini_pjt_interfaces__msg__Detection *)allocator.allocate(sizeof(mini_pjt_interfaces__msg__Detection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(mini_pjt_interfaces__msg__Detection));
  bool success = mini_pjt_interfaces__msg__Detection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
mini_pjt_interfaces__msg__Detection__destroy(mini_pjt_interfaces__msg__Detection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    mini_pjt_interfaces__msg__Detection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
mini_pjt_interfaces__msg__Detection__Sequence__init(mini_pjt_interfaces__msg__Detection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mini_pjt_interfaces__msg__Detection * data = NULL;

  if (size) {
    data = (mini_pjt_interfaces__msg__Detection *)allocator.zero_allocate(size, sizeof(mini_pjt_interfaces__msg__Detection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = mini_pjt_interfaces__msg__Detection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        mini_pjt_interfaces__msg__Detection__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
mini_pjt_interfaces__msg__Detection__Sequence__fini(mini_pjt_interfaces__msg__Detection__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      mini_pjt_interfaces__msg__Detection__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

mini_pjt_interfaces__msg__Detection__Sequence *
mini_pjt_interfaces__msg__Detection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  mini_pjt_interfaces__msg__Detection__Sequence * array = (mini_pjt_interfaces__msg__Detection__Sequence *)allocator.allocate(sizeof(mini_pjt_interfaces__msg__Detection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = mini_pjt_interfaces__msg__Detection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
mini_pjt_interfaces__msg__Detection__Sequence__destroy(mini_pjt_interfaces__msg__Detection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    mini_pjt_interfaces__msg__Detection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
mini_pjt_interfaces__msg__Detection__Sequence__are_equal(const mini_pjt_interfaces__msg__Detection__Sequence * lhs, const mini_pjt_interfaces__msg__Detection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!mini_pjt_interfaces__msg__Detection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
mini_pjt_interfaces__msg__Detection__Sequence__copy(
  const mini_pjt_interfaces__msg__Detection__Sequence * input,
  mini_pjt_interfaces__msg__Detection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(mini_pjt_interfaces__msg__Detection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    mini_pjt_interfaces__msg__Detection * data =
      (mini_pjt_interfaces__msg__Detection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!mini_pjt_interfaces__msg__Detection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          mini_pjt_interfaces__msg__Detection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!mini_pjt_interfaces__msg__Detection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
