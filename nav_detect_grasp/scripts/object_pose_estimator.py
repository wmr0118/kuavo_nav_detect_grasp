#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Object Pose Estimator Node for nav_detect_grasp demo
Integrates AprilTag and YOLO detection results to estimate object poses
"""

import rospy
import numpy as np
import cv2
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped, Point, Quaternion
from apriltag_ros.msg import AprilTagDetectionArray
from kuavo_msgs.msg import yoloDetection
from cv_bridge import CvBridge
import tf2_ros
import tf2_geometry_msgs
from tf.transformations import quaternion_from_euler, euler_from_quaternion
import threading
import time

class ObjectPoseEstimator:
    def __init__(self):
        rospy.init_node('object_pose_estimator', anonymous=True)
        
        # Initialize parameters
        self.use_apriltag = rospy.get_param('~use_apriltag', True)
        self.use_yolo = rospy.get_param('~use_yolo', True)
        self.apriltag_topic = rospy.get_param('~apriltag_topic', '/robot_tag_info')
        self.yolo_topic = rospy.get_param('~yolo_topic', '/yolo_detections')
        self.depth_topic = rospy.get_param('~depth_topic', '/camera/depth/image_rect_raw')
        self.camera_info_topic = rospy.get_param('~camera_info_topic', '/camera/color/camera_info')
        self.output_topic = rospy.get_param('~output_topic', '/target_pose')
        
        # Initialize variables
        self.bridge = CvBridge()
        self.latest_depth_image = None
        self.camera_matrix = None
        self.distortion_coeffs = None
        self.depth_scale = 0.001  # Depth scale factor (mm to m)
        
        # TF setup
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()
        
        # Threading
        self.data_lock = threading.Lock()
        
        # Setup publishers and subscribers
        self.pose_pub = rospy.Publisher(self.output_topic, PoseStamped, queue_size=10)
        
        if self.use_apriltag:
            self.apriltag_sub = rospy.Subscriber(self.apriltag_topic, AprilTagDetectionArray, self.apriltag_callback)
        
        if self.use_yolo:
            self.yolo_sub = rospy.Subscriber(self.yolo_topic, yoloDetection, self.yolo_callback)
        
        self.depth_sub = rospy.Subscriber(self.depth_topic, Image, self.depth_callback)
        self.camera_info_sub = rospy.Subscriber(self.camera_info_topic, CameraInfo, self.camera_info_callback)
        
        # Pose filtering
        self.pose_history = []
        self.max_history_size = 10
        
        rospy.loginfo("Object Pose Estimator initialized")
    
    def camera_info_callback(self, msg):
        """Callback for camera info messages"""
        if self.camera_matrix is None:
            self.camera_matrix = np.array(msg.K).reshape(3, 3)
            self.distortion_coeffs = np.array(msg.D)
            rospy.loginfo("Camera calibration parameters received")
    
    def depth_callback(self, msg):
        """Callback for depth image messages"""
        try:
            with self.data_lock:
                self.latest_depth_image = self.bridge.imgmsg_to_cv2(msg, "16UC1")
        except Exception as e:
            rospy.logerr(f"Error converting depth image: {e}")
    
    def apriltag_callback(self, msg):
        """Callback for AprilTag detection messages"""
        if not msg.detections:
            return
        
        try:
            for detection in msg.detections:
                # AprilTag already provides 3D pose in base_link frame
                pose = detection.pose.pose.pose
                
                # Create pose message
                pose_msg = PoseStamped()
                pose_msg.header.stamp = rospy.Time.now()
                pose_msg.header.frame_id = "base_link"
                pose_msg.pose = pose
                
                # Publish pose
                self.pose_pub.publish(pose_msg)
                rospy.loginfo(f"AprilTag pose published: {pose.position}")
                
        except Exception as e:
            rospy.logerr(f"Error processing AprilTag detection: {e}")
    
    def yolo_callback(self, msg):
        """Callback for YOLO detection messages"""
        if not msg.data or self.latest_depth_image is None or self.camera_matrix is None:
            return
        
        try:
            for detection in msg.data:
                # Get 2D detection center
                center_x = int(detection.x_pos)
                center_y = int(detection.y_pos)
                
                # Estimate 3D pose using depth information
                pose_3d = self.estimate_3d_pose_from_depth(center_x, center_y, detection)
                
                if pose_3d is not None:
                    # Create pose message
                    pose_msg = PoseStamped()
                    pose_msg.header.stamp = rospy.Time.now()
                    pose_msg.header.frame_id = "head_camera_color_optical_frame"
                    pose_msg.pose.position = pose_3d['position']
                    pose_msg.pose.orientation = pose_3d['orientation']
                    
                    # Transform to base_link frame
                    try:
                        transform = self.tf_buffer.lookup_transform(
                            'base_link', 
                            'head_camera_color_optical_frame', 
                            rospy.Time(0)
                        )
                        
                        pose_transformed = tf2_geometry_msgs.do_transform_pose(pose_msg, transform)
                        pose_transformed.header.frame_id = "base_link"
                        
                        # Publish transformed pose
                        self.pose_pub.publish(pose_transformed)
                        rospy.loginfo(f"YOLO pose published: {pose_transformed.pose.position}")
                        
                    except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
                        rospy.logwarn(f"TF transform failed: {e}")
                        # Publish in camera frame
                        self.pose_pub.publish(pose_msg)
                
        except Exception as e:
            rospy.logerr(f"Error processing YOLO detection: {e}")
    
    def estimate_3d_pose_from_depth(self, center_x, center_y, detection):
        """Estimate 3D pose from 2D detection and depth image"""
        try:
            # Sample depth around the detection center
            sample_size = 5
            half_size = sample_size // 2
            
            # Get depth samples
            depth_samples = []
            for i in range(-half_size, half_size + 1):
                for j in range(-half_size, half_size + 1):
                    x = center_x + i
                    y = center_y + j
                    if (0 <= x < self.latest_depth_image.shape[1] and 
                        0 <= y < self.latest_depth_image.shape[0]):
                        depth = self.latest_depth_image[y, x]
                        if depth > 0:
                            depth_samples.append(depth)
            
            if not depth_samples:
                return None
            
            # Use median depth for robustness
            depth_median = np.median(depth_samples)
            depth_meters = depth_median * self.depth_scale
            
            # Check depth range
            if depth_meters < 0.1 or depth_meters > 3.0:
                return None
            
            # Back-project to 3D
            fx = self.camera_matrix[0, 0]
            fy = self.camera_matrix[1, 1]
            cx = self.camera_matrix[0, 2]
            cy = self.camera_matrix[1, 2]
            
            # Convert from pixel to 3D coordinates
            x_3d = (center_x - cx) * depth_meters / fx
            y_3d = (center_y - cy) * depth_meters / fy
            z_3d = depth_meters
            
            # Create position
            position = Point()
            position.x = x_3d
            position.y = y_3d
            position.z = z_3d
            
            # Estimate orientation (simple approach: facing camera)
            # For more complex objects, you might want to use pose estimation networks
            orientation = Quaternion()
            orientation.x = 0.0
            orientation.y = 0.0
            orientation.z = 0.0
            orientation.w = 1.0
            
            return {
                'position': position,
                'orientation': orientation
            }
            
        except Exception as e:
            rospy.logerr(f"Error estimating 3D pose: {e}")
            return None
    
    def filter_pose(self, pose_msg):
        """Filter pose using moving average"""
        with self.data_lock:
            self.pose_history.append(pose_msg)
            if len(self.pose_history) > self.max_history_size:
                self.pose_history.pop(0)
            
            if len(self.pose_history) < 3:
                return pose_msg
            
            # Calculate filtered position
            positions = [msg.pose.position for msg in self.pose_history]
            filtered_position = Point()
            filtered_position.x = np.mean([p.x for p in positions])
            filtered_position.y = np.mean([p.y for p in positions])
            filtered_position.z = np.mean([p.z for p in positions])
            
            # Create filtered pose message
            filtered_pose = PoseStamped()
            filtered_pose.header = pose_msg.header
            filtered_pose.pose.position = filtered_position
            filtered_pose.pose.orientation = pose_msg.pose.orientation
            
            return filtered_pose
    
    def run(self):
        """Main run loop"""
        rospy.loginfo("Object Pose Estimator started")
        rospy.spin()

def main():
    try:
        node = ObjectPoseEstimator()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Object Pose Estimator interrupted")
    except Exception as e:
        rospy.logerr(f"Object Pose Estimator error: {e}")

if __name__ == '__main__':
    main() 