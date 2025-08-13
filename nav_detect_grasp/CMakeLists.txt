cmake_minimum_required(VERSION 3.0.2)
project(nav_detect_grasp)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  nav_msgs
  sensor_msgs
  apriltag_ros
  kuavo_msgs
  tf2_ros
  tf2_geometry_msgs
  cv_bridge
  image_transport
)

catkin_package(
  CATKIN_DEPENDS
    rospy
    std_msgs
    geometry_msgs
    nav_msgs
    sensor_msgs
    apriltag_ros
    kuavo_msgs
    tf2_ros
    tf2_geometry_msgs
    cv_bridge
    image_transport
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/nav_detect_grasp_demo.py
  scripts/object_pose_estimator.py
  scripts/yolo_detection_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
) 