// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from mini_pjt_interfaces:msg/RobotState.idl
// generated code does not contain a copyright notice

#ifndef MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_HPP_
#define MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__mini_pjt_interfaces__msg__RobotState __attribute__((deprecated))
#else
# define DEPRECATED__mini_pjt_interfaces__msg__RobotState __declspec(deprecated)
#endif

namespace mini_pjt_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct RobotState_
{
  using Type = RobotState_<ContainerAllocator>;

  explicit RobotState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->state = "";
      this->target_distance = 0.0f;
      this->arrived = false;
    }
  }

  explicit RobotState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    state(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->state = "";
      this->target_distance = 0.0f;
      this->arrived = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _state_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _state_type state;
  using _target_distance_type =
    float;
  _target_distance_type target_distance;
  using _arrived_type =
    bool;
  _arrived_type arrived;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__state(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->state = _arg;
    return *this;
  }
  Type & set__target_distance(
    const float & _arg)
  {
    this->target_distance = _arg;
    return *this;
  }
  Type & set__arrived(
    const bool & _arg)
  {
    this->arrived = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> *;
  using ConstRawPtr =
    const mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__mini_pjt_interfaces__msg__RobotState
    std::shared_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__mini_pjt_interfaces__msg__RobotState
    std::shared_ptr<mini_pjt_interfaces::msg::RobotState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RobotState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->state != other.state) {
      return false;
    }
    if (this->target_distance != other.target_distance) {
      return false;
    }
    if (this->arrived != other.arrived) {
      return false;
    }
    return true;
  }
  bool operator!=(const RobotState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RobotState_

// alias to use template instance with default allocator
using RobotState =
  mini_pjt_interfaces::msg::RobotState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace mini_pjt_interfaces

#endif  // MINI_PJT_INTERFACES__MSG__DETAIL__ROBOT_STATE__STRUCT_HPP_
