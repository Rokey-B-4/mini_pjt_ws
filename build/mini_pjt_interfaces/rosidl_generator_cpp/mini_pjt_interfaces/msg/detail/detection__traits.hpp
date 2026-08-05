// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from mini_pjt_interfaces:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "mini_pjt_interfaces/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace mini_pjt_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const Detection & msg,
  std::ostream & out)
{
  out << "{";
  // member: class_name
  {
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: center_x
  {
    out << "center_x: ";
    rosidl_generator_traits::value_to_yaml(msg.center_x, out);
    out << ", ";
  }

  // member: center_y
  {
    out << "center_y: ";
    rosidl_generator_traits::value_to_yaml(msg.center_y, out);
    out << ", ";
  }

  // member: bbox
  {
    if (msg.bbox.size() == 0) {
      out << "bbox: []";
    } else {
      out << "bbox: [";
      size_t pending_items = msg.bbox.size();
      for (auto item : msg.bbox) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Detection & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: class_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: center_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_x: ";
    rosidl_generator_traits::value_to_yaml(msg.center_x, out);
    out << "\n";
  }

  // member: center_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_y: ";
    rosidl_generator_traits::value_to_yaml(msg.center_y, out);
    out << "\n";
  }

  // member: bbox
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.bbox.size() == 0) {
      out << "bbox: []\n";
    } else {
      out << "bbox:\n";
      for (auto item : msg.bbox) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Detection & msg, bool use_flow_style = false)
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
  const mini_pjt_interfaces::msg::Detection & msg,
  std::ostream & out, size_t indentation = 0)
{
  mini_pjt_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use mini_pjt_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const mini_pjt_interfaces::msg::Detection & msg)
{
  return mini_pjt_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<mini_pjt_interfaces::msg::Detection>()
{
  return "mini_pjt_interfaces::msg::Detection";
}

template<>
inline const char * name<mini_pjt_interfaces::msg::Detection>()
{
  return "mini_pjt_interfaces/msg/Detection";
}

template<>
struct has_fixed_size<mini_pjt_interfaces::msg::Detection>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<mini_pjt_interfaces::msg::Detection>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<mini_pjt_interfaces::msg::Detection>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__DETECTION__TRAITS_HPP_
