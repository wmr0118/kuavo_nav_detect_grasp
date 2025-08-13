#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YOLO Detection Node for nav_detect_grasp demo
Integrates with existing YOLO detection functionality
"""

import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image, CameraInfo
from kuavo_msgs.msg import yoloDetection, yoloOutputData
from cv_bridge import CvBridge
import threading
import time

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    rospy.logwarn("Ultralytics YOLO not available. Install with: pip install ultralytics")

class YOLODetectionNode:
    def __init__(self):
        rospy.init_node('yolo_detection_node', anonymous=True)
        
        # Initialize parameters
        self.model_path = rospy.get_param('~model_path', 'yolov8n.pt')
        self.confidence_threshold = rospy.get_param('~confidence_threshold', 0.5)
        self.image_topic = rospy.get_param('~image_topic', '/camera/color/image_raw')
        self.camera_info_topic = rospy.get_param('~camera_info_topic', '/camera/color/camera_info')
        
        # Initialize variables
        self.bridge = CvBridge()
        self.latest_image = None
        self.camera_matrix = None
        self.distortion_coeffs = None
        self.image_lock = threading.Lock()
        
        # Initialize YOLO model
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(self.model_path)
                rospy.loginfo(f"YOLO model loaded successfully from {self.model_path}")
            except Exception as e:
                rospy.logerr(f"Failed to load YOLO model: {e}")
                self.model = None
        else:
            self.model = None
            rospy.logerr("YOLO not available, node will not function properly")
        
        # Setup publishers and subscribers
        self.detection_pub = rospy.Publisher('/yolo_detections', yoloDetection, queue_size=10)
        self.image_sub = rospy.Subscriber(self.image_topic, Image, self.image_callback)
        self.camera_info_sub = rospy.Subscriber(self.camera_info_topic, CameraInfo, self.camera_info_callback)
        
        # Detection timer
        self.detection_timer = rospy.Timer(rospy.Duration(0.1), self.detection_timer_callback)
        
        rospy.loginfo("YOLO Detection Node initialized")
    
    def image_callback(self, msg):
        """Callback for image messages"""
        try:
            with self.image_lock:
                self.latest_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            rospy.logerr(f"Error converting image: {e}")
    
    def camera_info_callback(self, msg):
        """Callback for camera info messages"""
        if self.camera_matrix is None:
            self.camera_matrix = np.array(msg.K).reshape(3, 3)
            self.distortion_coeffs = np.array(msg.D)
            rospy.loginfo("Camera calibration parameters received")
    
    def detection_timer_callback(self, event):
        """Timer callback for running detection"""
        if self.model is None or self.latest_image is None:
            return
        
        try:
            # Run YOLO detection
            results = self.model(self.latest_image, conf=self.confidence_threshold)
            
            # Convert results to ROS message
            detection_msg = self.convert_results_to_msg(results)
            
            # Publish detections
            if detection_msg.data:
                self.detection_pub.publish(detection_msg)
                
        except Exception as e:
            rospy.logerr(f"Error in detection: {e}")
    
    def convert_results_to_msg(self, results):
        """Convert YOLO results to ROS message"""
        detection_msg = yoloDetection()
        detection_msg.header.stamp = rospy.Time.now()
        detection_msg.header.frame_id = "head_camera_color_optical_frame"
        
        if not results:
            return detection_msg
        
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    if box.conf >= self.confidence_threshold:
                        # Create detection data
                        detection_data = yoloOutputData()
                        detection_data.class_name = result.names[int(box.cls)]
                        detection_data.class_id = int(box.cls)
                        detection_data.confidence = float(box.conf)
                        
                        # Box coordinates (center x, center y, width, height)
                        detection_data.x_pos = float(box.xywh[0])
                        detection_data.y_pos = float(box.xywh[1])
                        detection_data.width = float(box.xywh[2])
                        detection_data.height = float(box.xywh[3])
                        
                        detection_msg.data.append(detection_data)
        
        return detection_msg
    
    def run(self):
        """Main run loop"""
        rospy.loginfo("YOLO Detection Node started")
        rospy.spin()

def main():
    try:
        node = YOLODetectionNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("YOLO Detection Node interrupted")
    except Exception as e:
        rospy.logerr(f"YOLO Detection Node error: {e}")

if __name__ == '__main__':
    main() 