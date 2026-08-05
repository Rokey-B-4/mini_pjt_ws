// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from mini_pjt_interfaces:msg/RobotState.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__BUILDER_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "mini_pjt_interfaces/msg/detail/robot_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace mini_pjt_interfaces
{

namespace msg
{

namespace builder
{

class Init_RobotState_arrived
{
public:
  explicit Init_RobotState_arrived(::mini_pjt_interfaces::msg::RobotState & msg)
  : msg_(msg)
  {}
  ::mini_pjt_interfaces::msg::RobotState arrived(::mini_pjt_interfaces::msg::RobotState::_arrived_type arg)
  {
    msg_.arrived = std::move(arg);
    return std::move(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::RobotState msg_;
};

class Init_RobotState_target_distance
{
public:
  explicit Init_RobotState_target_distance(::mini_pjt_interfaces::msg::RobotState & msg)
  : msg_(msg)
  {}
  Init_RobotState_arrived target_distance(::mini_pjt_interfaces::msg::RobotState::_target_distance_type arg)
  {
    msg_.target_distance = std::move(arg);
    return Init_RobotState_arrived(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::RobotState msg_;
};

class Init_RobotState_state
{
public:
  explicit Init_RobotState_state(::mini_pjt_interfaces::msg::RobotState & msg)
  : msg_(msg)
  {}
  Init_RobotState_target_distance state(::mini_pjt_interfaces::msg::RobotState::_state_type arg)
  {
    msg_.state = std::move(arg);
    return Init_RobotState_target_distance(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::RobotState msg_;
};

class Init_RobotState_header
{
public:
  Init_RobotState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RobotState_state header(::mini_pjt_interfaces::msg::RobotState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_RobotState_state(msg_);
  }

private:
  ::mini_pjt_interfaces::msg::RobotState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::mini_pjt_interfaces::msg::RobotState>()
{
  return mini_pjt_interfaces::msg::builder::Init_RobotState_header();
}

}  // namespace mini_pjt_interfaces

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__BUILDER_HPP_
