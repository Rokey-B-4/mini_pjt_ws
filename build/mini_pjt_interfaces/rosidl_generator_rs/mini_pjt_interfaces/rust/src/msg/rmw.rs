#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "mini_pjt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__Detection() -> *const std::ffi::c_void;
}

#[link(name = "mini_pjt_interfaces__rosidl_generator_c")]
extern "C" {
    fn mini_pjt_interfaces__msg__Detection__init(msg: *mut Detection) -> bool;
    fn mini_pjt_interfaces__msg__Detection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Detection>, size: usize) -> bool;
    fn mini_pjt_interfaces__msg__Detection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Detection>);
    fn mini_pjt_interfaces__msg__Detection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Detection>, out_seq: *mut rosidl_runtime_rs::Sequence<Detection>) -> bool;
}

// Corresponds to mini_pjt_interfaces__msg__Detection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// 단일 객체 검출 결과 (웹캠 / 온보드 공용)

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {
    /// 클래스 이름 (예: "car", "dummy")
    pub class_name: rosidl_runtime_rs::String,

    /// 검출 신뢰도 0.0 ~ 1.0
    pub confidence: f32,

    /// bbox 중심 픽셀 좌표
    pub center_x: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_y: i32,

    /// bbox 픽셀 좌표 [x1, y1, x2, y2]
    pub bbox: [i32; 4],

}



impl Default for Detection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !mini_pjt_interfaces__msg__Detection__init(&mut msg as *mut _) {
        panic!("Call to mini_pjt_interfaces__msg__Detection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Detection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__Detection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__Detection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__Detection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Detection where Self: Sized {
  const TYPE_NAME: &'static str = "mini_pjt_interfaces/msg/Detection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__Detection() }
  }
}


#[link(name = "mini_pjt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__DetectionArray() -> *const std::ffi::c_void;
}

#[link(name = "mini_pjt_interfaces__rosidl_generator_c")]
extern "C" {
    fn mini_pjt_interfaces__msg__DetectionArray__init(msg: *mut DetectionArray) -> bool;
    fn mini_pjt_interfaces__msg__DetectionArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>, size: usize) -> bool;
    fn mini_pjt_interfaces__msg__DetectionArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>);
    fn mini_pjt_interfaces__msg__DetectionArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DetectionArray>, out_seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>) -> bool;
}

// Corresponds to mini_pjt_interfaces__msg__DetectionArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// 한 프레임에서 나온 검출 결과 묶음
/// header.stamp 은 추론에 사용한 원본 이미지의 타임스탬프를 그대로 넣는다.
/// header.frame_id 는 카메라 프레임 (예: "webcam", "oakd_rgb_camera_optical_frame")

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Detection>,

}



impl Default for DetectionArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !mini_pjt_interfaces__msg__DetectionArray__init(&mut msg as *mut _) {
        panic!("Call to mini_pjt_interfaces__msg__DetectionArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DetectionArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__DetectionArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__DetectionArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__DetectionArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DetectionArray where Self: Sized {
  const TYPE_NAME: &'static str = "mini_pjt_interfaces/msg/DetectionArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__DetectionArray() }
  }
}


#[link(name = "mini_pjt_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__RobotState() -> *const std::ffi::c_void;
}

#[link(name = "mini_pjt_interfaces__rosidl_generator_c")]
extern "C" {
    fn mini_pjt_interfaces__msg__RobotState__init(msg: *mut RobotState) -> bool;
    fn mini_pjt_interfaces__msg__RobotState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RobotState>, size: usize) -> bool;
    fn mini_pjt_interfaces__msg__RobotState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RobotState>);
    fn mini_pjt_interfaces__msg__RobotState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RobotState>, out_seq: *mut rosidl_runtime_rs::Sequence<RobotState>) -> bool;
}

// Corresponds to mini_pjt_interfaces__msg__RobotState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// 미션 상태머신 / 접근 제어 노드가 발행하는 로봇 상태

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RobotState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,

    /// 상태 문자열
    ///   INIT, READY, UNDOCKING, NAVIGATING, ARRIVED,
    ///   SEARCHING, APPROACHING, REACHED, DOCKING, DONE, FAILED, ABORTED
    pub state: rosidl_runtime_rs::String,

    /// 목표(rc_car)까지의 거리. 미측정 시 -1.0
    pub target_distance: f32,

    /// 목표 거리 임계값(기본 0.3m) 이내 도달 여부
    pub arrived: bool,

}



impl Default for RobotState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !mini_pjt_interfaces__msg__RobotState__init(&mut msg as *mut _) {
        panic!("Call to mini_pjt_interfaces__msg__RobotState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RobotState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__RobotState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__RobotState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { mini_pjt_interfaces__msg__RobotState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RobotState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RobotState where Self: Sized {
  const TYPE_NAME: &'static str = "mini_pjt_interfaces/msg/RobotState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__mini_pjt_interfaces__msg__RobotState() }
  }
}


