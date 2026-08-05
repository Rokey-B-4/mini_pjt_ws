// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from mini_pjt_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "mini_pjt_interfaces/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace mini_pjt_interfaces
{

namespace msg
{

namespace builder
{

class Init_Detection_bbox
{
public:
  explicit Init_Detection_bbox(::mini_pjt_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  ::mini_pjt_interfaces::msg::Detection bbox(::mini_pjt_interfaces::msg::Detection::_bbox_type arg)
  {
    msg_.bbox = std::move(arg);
    return std::move(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::Detection msg_;
};

class Init_Detection_center_y
{
public:
  explicit Init_Detection_center_y(::mini_pjt_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox center_y(::mini_pjt_interfaces::msg::Detection::_center_y_type arg)
  {
    msg_.center_y = std::move(arg);
    return Init_Detection_bbox(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::Detection msg_;
};

class Init_Detection_center_x
{
public:
  explicit Init_Detection_center_x(::mini_pjt_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_y center_x(::mini_pjt_interfaces::msg::Detection::_center_x_type arg)
  {
    msg_.center_x = std::move(arg);
    return Init_Detection_center_y(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::Detection msg_;
};

class Init_Detection_confidence
{
public:
  explicit Init_Detection_confidence(::mini_pjt_interfaces::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_x confidence(::mini_pjt_interfaces::msg::Detection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_Detection_center_x(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::Detection msg_;
};

class Init_Detection_class_name
{
public:
  Init_Detection_class_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection_confidence class_name(::mini_pjt_interfaces::msg::Detection::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection_confidence(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::Detection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::mini_pjt_interfaces::msg::Detection>()
{
  return mini_pjt_interfaces::msg::builder::Init_Detection_class_name();
}

}  // namespace mini_pjt_interfaces

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__BUILDER_HPP_
