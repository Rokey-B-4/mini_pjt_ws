// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from mini_pjt_interfaces:msg/RobotState.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__TRAITS_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "mini_pjt_interfaces/msg/detail/robot_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace mini_pjt_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const RobotState & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: state
  {
    out << "state: ";
    rosidl_generator_traits::value_to_yaml(msg.state, out);
    out << ", ";
  }

  // member: target_distance
  {
    out << "target_distance: ";
    rosidl_generator_traits::value_to_yaml(msg.target_distance, out);
    out << ", ";
  }

  // member: arrived
  {
    out << "arrived: ";
    rosidl_generator_traits::value_to_yaml(msg.arrived, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const RobotState & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "state: ";
    rosidl_generator_traits::value_to_yaml(msg.state, out);
    out << "\n";
  }

  // member: target_distance
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "target_distance: ";
    rosidl_generator_traits::value_to_yaml(msg.target_distance, out);
    out << "\n";
  }

  // member: arrived
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "arrived: ";
    rosidl_generator_traits::value_to_yaml(msg.arrived, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const RobotState & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace mini_pjt_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use mini_pjt_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const mini_pjt_interfaces::msg::RobotState & msg,
  std::ostream & out, size_t indentation = 0)
{
  mini_pjt_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use mini_pjt_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const mini_pjt_interfaces::msg::RobotState & msg)
{
  return mini_pjt_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<mini_pjt_interfaces::msg::RobotState>()
{
  return "mini_pjt_interfaces::msg::RobotState";
}

template<>
inline const char * name<mini_pjt_interfaces::msg::RobotState>()
{
  return "mini_pjt_interfaces/msg/RobotState";
}

template<>
struct has_fixed_size<mini_pjt_interfaces::msg::RobotState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<mini_pjt_interfaces::msg::RobotState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<mini_pjt_interfaces::msg::RobotState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__TRAITS_HPP_
