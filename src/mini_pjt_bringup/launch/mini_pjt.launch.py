#!/usr/bin/env python3
"""
mini_pjt 전체 노드 통합 런치 (skeleton)

사용 예:
  ros2 launch mini_pjt_bringup mini_pjt.launch.py
  ros2 launch mini_pjt_bringup mini_pjt.launch.py dry_run:=false
  ros2 launch mini_pjt_bringup mini_pjt.launch.py enable_webcam:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('mini_pjt_bringup')
    default_params = os.path.join(bringup_share, 'config', 'params.yaml')

    params_file = LaunchConfiguration('params_file')
    dry_run = LaunchConfiguration('dry_run')
    enable_webcam = LaunchConfiguration('enable_webcam')
    enable_onboard = LaunchConfiguration('enable_onboard')

    args = [
        DeclareLaunchArgument('params_file', default_value=default_params,
                              description='통합 파라미터 yaml 경로'),
        DeclareLaunchArgument('dry_run', default_value='true',
                              description='true 면 Nav2/dock 호출 없이 상태머신만 동작'),
        DeclareLaunchArgument('enable_webcam', default_value='true',
                              description='웹캠 검출 노드 실행 여부'),
        DeclareLaunchArgument('enable_onboard', default_value='true',
                              description='OAK-D 온보드 검출 노드 실행 여부 (로봇 필요)'),
    ]

    nodes = [
        Node(
            package='mini_pjt_vision',
            executable='webcam_detector_node',
            name='webcam_detector_node',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(enable_webcam),
        ),
        Node(
            package='mini_pjt_vision',
            executable='robot_detector_node',
            name='robot_detector_node',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(enable_onboard),
        ),
        Node(
            package='mini_pjt_control',
            executable='mission_manager_node',
            name='mission_manager_node',
            output='screen',
            parameters=[params_file, {'dry_run': dry_run}],
        ),
        Node(
            package='mini_pjt_control',
            executable='approach_controller',
            name='approach_controller',
            output='screen',
            parameters=[params_file],
        ),
    ]

    return LaunchDescription(args + nodes)
