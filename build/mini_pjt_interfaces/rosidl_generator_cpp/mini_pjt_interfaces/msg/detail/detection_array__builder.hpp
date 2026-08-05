// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from mini_pjt_interfaces:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "mini_pjt_interfaces/msg/detail/detection_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace mini_pjt_interfaces
{

namespace msg
{

namespace builder
{

class Init_DetectionArray_detections
{
public:
  explicit Init_DetectionArray_detections(::mini_pjt_interfaces::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  ::mini_pjt_interfaces::msg::DetectionArray detections(::mini_pjt_interfaces::msg::DetectionArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return std::move(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::DetectionArray msg_;
};

class Init_DetectionArray_header
{
public:
  Init_DetectionArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectionArray_detections header(::mini_pjt_interfaces::msg::DetectionArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectionArray_detections(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::DetectionArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::mini_pjt_interfaces::msg::DetectionArray>()
{
  return mini_pjt_interfaces::msg::builder::Init_DetectionArray_header();
}

}  // namespace mini_pjt_interfaces

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
