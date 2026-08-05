#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to mini_pjt_interfaces__msg__Detection
/// 단일 객체 검출 결과 (웹캠 / 온보드 공용)

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {
    /// 클래스 이름 (예: "car", "dummy")
    pub class_name: std::string::String,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Detection::default())
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = super::msg::rmw::Detection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        class_name: msg.class_name.as_str().into(),
        confidence: msg.confidence,
        center_x: msg.center_x,
        center_y: msg.center_y,
        bbox: msg.bbox,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        class_name: msg.class_name.as_str().into(),
      confidence: msg.confidence,
      center_x: msg.center_x,
      center_y: msg.center_y,
        bbox: msg.bbox,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      class_name: msg.class_name.to_string(),
      confidence: msg.confidence,
      center_x: msg.center_x,
      center_y: msg.center_y,
      bbox: msg.bbox,
    }
  }
}


// Corresponds to mini_pjt_interfaces__msg__DetectionArray
/// 한 프레임에서 나온 검출 결과 묶음
/// header.stamp 은 추론에 사용한 원본 이미지의 타임스탬프를 그대로 넣는다.
/// header.frame_id 는 카메라 프레임 (예: "webcam", "oakd_rgb_camera_optical_frame")

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: Vec<super::msg::Detection>,

}



impl Default for DetectionArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DetectionArray::default())
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = super::msg::rmw::DetectionArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detections: msg.detections
          .into_iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        detections: msg.detections
          .iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detections: msg.detections
          .into_iter()
          .map(super::msg::Detection::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to mini_pjt_interfaces__msg__RobotState
/// 미션 상태머신 / 접근 제어 노드가 발행하는 로봇 상태

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RobotState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,

    /// 상태 문자열
    ///   INIT, READY, UNDOCKING, NAVIGATING, ARRIVED,
    ///   SEARCHING, APPROACHING, REACHED, DOCKING, DONE, FAILED, ABORTED
    pub state: std::string::String,

    /// 목표(rc_car)까지의 거리. 미측정 시 -1.0
    pub target_distance: f32,

    /// 목표 거리 임계값(기본 0.3m) 이내 도달 여부
    pub arrived: bool,

}



impl Default for RobotState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RobotState::default())
  }
}

impl rosidl_runtime_rs::Message for RobotState {
  type RmwMsg = super::msg::rmw::RobotState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        state: msg.state.as_str().into(),
        target_distance: msg.target_distance,
        arrived: msg.arrived,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        state: msg.state.as_str().into(),
      target_distance: msg.target_distance,
      arrived: msg.arrived,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      state: msg.state.to_string(),
      target_distance: msg.target_distance,
      arrived: msg.arrived,
    }
  }
}


