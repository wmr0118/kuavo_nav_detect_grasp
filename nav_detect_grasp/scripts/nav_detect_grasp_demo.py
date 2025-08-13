#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Navigation, Detection and Grasp Demo for Kuavo Robot
Main demo node that coordinates navigation, object detection, and grasping
"""

import rospy
import numpy as np
import math
import time
import threading
from geometry_msgs.msg import PoseStamped, Twist, Point, Quaternion
from nav_msgs.msg import Odometry
from kuavo_msgs.msg import armTargetPoses, robotHandPosition
from kuavo_msgs.srv import changeArmCtrlMode, changeArmCtrlModeRequest
from kuavo_msgs.srv import twoArmHandPoseCmdSrv, twoArmHandPoseCmd, ikSolveParam
from tf.transformations import quaternion_from_euler, euler_from_quaternion
import tf2_ros
import tf2_geometry_msgs

class NavDetectGraspDemo:
    def __init__(self):
        rospy.init_node('nav_detect_grasp_demo', anonymous=True)
        
        # Load parameters
        self.load_parameters()
        
        # Initialize state
        self.current_pose = None
        self.target_pose = None
        self.demo_state = "IDLE"
        self.is_running = False
        
        # TF setup
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        
        # Setup publishers and subscribers
        self.setup_ros_components()
        
        # Demo thread
        self.demo_thread = threading.Thread(target=self.demo_loop)
        self.demo_thread.daemon = True
        
        rospy.loginfo("Navigation, Detection and Grasp Demo initialized")
    
    def load_parameters(self):
        """Load parameters from parameter server"""
        # Navigation parameters
        self.nav_config = rospy.get_param('~nav_config', '')
        self.detection_config = rospy.get_param('~detection_config', '')
        self.grasp_config = rospy.get_param('~grasp_config', '')
        
        # Demo parameters
        self.use_simulation = rospy.get_param('~use_simulation', False)
        self.use_camera = rospy.get_param('~use_camera', True)
        self.use_apriltag_detection = rospy.get_param('~use_apriltag_detection', True)
        self.use_yolo_detection = rospy.get_param('~use_yolo_detection', True)
        
        # Load config files if available
        if self.nav_config:
            rospy.loginfo(f"Loading navigation config from: {self.nav_config}")
        if self.detection_config:
            rospy.loginfo(f"Loading detection config from: {self.detection_config}")
        if self.grasp_config:
            rospy.loginfo(f"Loading grasp config from: {self.grasp_config}")
    
    def setup_ros_components(self):
        """Setup ROS publishers and subscribers"""
        # Publishers
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.cmd_pose_pub = rospy.Publisher('/cmd_pose', Twist, queue_size=10)
        self.arm_target_pub = rospy.Publisher('/kuavo_arm_target_poses', armTargetPoses, queue_size=10)
        self.hand_control_pub = rospy.Publisher('/control_robot_hand_position', robotHandPosition, queue_size=10)
        
        # Subscribers
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        self.target_pose_sub = rospy.Subscriber('/target_pose', PoseStamped, self.target_pose_callback)
        
        # Service clients
        self.arm_mode_client = rospy.ServiceProxy('/arm_traj_change_mode', changeArmCtrlMode)
        self.ik_client = rospy.ServiceProxy('/ik/two_arm_hand_pose_cmd_srv', twoArmHandPoseCmdSrv)
        
        # Wait for services
        rospy.wait_for_service('/arm_traj_change_mode')
        rospy.wait_for_service('/ik/two_arm_hand_pose_cmd_srv')
    
    def odom_callback(self, msg):
        """Callback for odometry messages"""
        self.current_pose = msg.pose.pose
    
    def target_pose_callback(self, msg):
        """Callback for target pose messages"""
        self.target_pose = msg.pose
    
    def start_demo(self):
        """Start the demo"""
        if self.is_running:
            rospy.logwarn("Demo is already running")
            return
        
        self.is_running = True
        self.demo_thread.start()
        rospy.loginfo("Demo started")
    
    def stop_demo(self):
        """Stop the demo"""
        self.is_running = False
        self.demo_state = "IDLE"
        rospy.loginfo("Demo stopped")
    
    def demo_loop(self):
        """Main demo loop"""
        try:
            # Wait for initial pose
            while self.current_pose is None and self.is_running:
                rospy.sleep(0.1)
            
            if not self.is_running:
                return
            
            rospy.loginfo("Starting demo sequence...")
            
            # Demo sequence
            self.demo_state = "NAVIGATE_TO_TARGET"
            if not self.navigate_to_target():
                rospy.logerr("Navigation to target failed")
                return
            
            self.demo_state = "DETECT_OBJECT"
            if not self.detect_object():
                rospy.logerr("Object detection failed")
                return
            
            self.demo_state = "APPROACH_OBJECT"
            if not self.approach_object():
                rospy.logerr("Approaching object failed")
                return
            
            self.demo_state = "GRASP_OBJECT"
            if not self.grasp_object():
                rospy.logerr("Grasping object failed")
                return
            
            self.demo_state = "NAVIGATE_TO_PLACE"
            if not self.navigate_to_place():
                rospy.logerr("Navigation to place failed")
                return
            
            self.demo_state = "PLACE_OBJECT"
            if not self.place_object():
                rospy.logerr("Placing object failed")
                return
            
            self.demo_state = "RETURN_HOME"
            if not self.return_home():
                rospy.logerr("Returning home failed")
                return
            
            rospy.loginfo("Demo completed successfully!")
            self.demo_state = "COMPLETED"
            
        except Exception as e:
            rospy.logerr(f"Demo error: {e}")
            self.demo_state = "ERROR"
        finally:
            self.is_running = False
    
    def navigate_to_target(self):
        """Navigate to target area"""
        rospy.loginfo("Navigating to target area...")
        
        # Simple navigation: move forward 1 meter
        cmd_pose = Twist()
        cmd_pose.linear.x = 1.0
        cmd_pose.linear.y = 0.0
        cmd_pose.linear.z = 0.0
        cmd_pose.angular.z = 0.0
        
        self.cmd_pose_pub.publish(cmd_pose)
        
        # Wait for navigation to complete
        start_time = time.time()
        while time.time() - start_time < 10.0 and self.is_running:
            rospy.sleep(0.1)
        
        # Stop movement
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)
        
        rospy.loginfo("Navigation to target completed")
        return True
    
    def detect_object(self):
        """Detect target object"""
        rospy.loginfo("Detecting target object...")
        
        # Wait for target pose
        start_time = time.time()
        while self.target_pose is None and time.time() - start_time < 10.0 and self.is_running:
            rospy.sleep(0.1)
        
        if self.target_pose is None:
            rospy.logwarn("No target pose received")
            return False
        
        rospy.loginfo(f"Target detected at: {self.target_pose.position}")
        return True
    
    def approach_object(self):
        """Approach the detected object"""
        rospy.loginfo("Approaching target object...")
        
        if self.target_pose is None:
            return False
        
        # Calculate approach position
        approach_distance = 0.3
        target_pos = self.target_pose.position
        
        # Move to approach position
        cmd_pose = Twist()
        cmd_pose.linear.x = target_pos.x - approach_distance
        cmd_pose.linear.y = target_pos.y
        cmd_pose.linear.z = 0.0
        cmd_pose.angular.z = 0.0
        
        self.cmd_pose_pub.publish(cmd_pose)
        
        # Wait for approach to complete
        start_time = time.time()
        while time.time() - start_time < 8.0 and self.is_running:
            rospy.sleep(0.1)
        
        # Stop movement
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)
        
        rospy.loginfo("Approach completed")
        return True
    
    def grasp_object(self):
        """Grasp the target object"""
        rospy.loginfo("Grasping target object...")
        
        if self.target_pose is None:
            return False
        
        try:
            # Set arm control mode to external control
            arm_mode_req = changeArmCtrlModeRequest()
            arm_mode_req.control_mode = 2  # External control
            arm_mode_resp = self.arm_mode_client(arm_mode_req)
            
            if not arm_mode_resp.result:
                rospy.logerr("Failed to set arm control mode")
                return False
            
            # Calculate grasp pose
            grasp_pose = self.calculate_grasp_pose()
            
            # Call IK service
            ik_req = twoArmHandPoseCmd()
            ik_req.use_custom_ik_param = True
            ik_req.joint_angles_as_q0 = False
            
            # Set left hand pose
            ik_req.hand_poses.left_pose.pos_xyz = np.array([grasp_pose[0], grasp_pose[1], grasp_pose[2]])
            ik_req.hand_poses.left_pose.quat_xyzw = grasp_pose[3:7]
            ik_req.hand_poses.left_pose.elbow_pos_xyz = np.zeros(3)
            
            # Set right hand pose (keep at current position)
            ik_req.hand_poses.right_pose.pos_xyz = np.array([0.0, 0.0, 0.0])
            ik_req.hand_poses.right_pose.quat_xyzw = [0.0, 0.0, 0.0, 1.0]
            ik_req.hand_poses.right_pose.elbow_pos_xyz = np.zeros(3)
            
            # Call IK
            ik_resp = self.ik_client(ik_req)
            
            if not ik_resp.success:
                rospy.logerr("IK solving failed")
                return False
            
            # Execute grasp trajectory
            self.execute_grasp_trajectory(ik_resp)
            
            rospy.loginfo("Grasp completed")
            return True
            
        except Exception as e:
            rospy.logerr(f"Grasp error: {e}")
            return False
    
    def calculate_grasp_pose(self):
        """Calculate grasp pose for the target object"""
        if self.target_pose is None:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        
        target_pos = self.target_pose.position
        
        # Simple grasp pose calculation
        grasp_x = target_pos.x
        grasp_y = target_pos.y
        grasp_z = target_pos.z + 0.05  # Slightly above target
        
        # Grasp orientation (facing forward)
        grasp_quat = quaternion_from_euler(0, -math.pi/2, 0)
        
        return [grasp_x, grasp_y, grasp_z, grasp_quat[0], grasp_quat[1], grasp_quat[2], grasp_quat[3]]
    
    def execute_grasp_trajectory(self, ik_result):
        """Execute the grasp trajectory"""
        try:
            # Get joint angles from IK result
            left_joints = ik_result.hand_poses.left_pose.joint_angles
            right_joints = ik_result.hand_poses.right_pose.joint_angles
            
            # Convert to degrees
            left_joints_deg = [math.degrees(angle) for angle in left_joints]
            right_joints_deg = [math.degrees(angle) for angle in right_joints]
            
            # Combine joint angles
            all_joints = left_joints_deg + right_joints_deg
            
            # Create trajectory message
            trajectory_msg = armTargetPoses()
            trajectory_msg.times = [3.0]  # 3 seconds to reach target
            trajectory_msg.values = all_joints
            
            # Publish trajectory
            self.arm_target_pub.publish(trajectory_msg)
            
            # Wait for execution
            rospy.sleep(3.0)
            
            # Close gripper
            self.close_gripper()
            
        except Exception as e:
            rospy.logerr(f"Trajectory execution error: {e}")
    
    def close_gripper(self):
        """Close the gripper"""
        try:
            hand_msg = robotHandPosition()
            hand_msg.left_hand_position = [90, 90, 90, 90, 90, 90]  # Close left hand
            hand_msg.right_hand_position = [90, 90, 90, 90, 90, 90]  # Close right hand
            
            self.hand_control_pub.publish(hand_msg)
            rospy.sleep(1.0)
            
        except Exception as e:
            rospy.logerr(f"Gripper control error: {e}")
    
    def navigate_to_place(self):
        """Navigate to place area"""
        rospy.loginfo("Navigating to place area...")
        
        # Simple navigation: move to place position
        cmd_pose = Twist()
        cmd_pose.linear.x = 1.0
        cmd_pose.linear.y = 0.5
        cmd_pose.linear.z = 0.0
        cmd_pose.angular.z = math.pi/4  # 45 degrees
        
        self.cmd_pose_pub.publish(cmd_pose)
        
        # Wait for navigation to complete
        start_time = time.time()
        while time.time() - start_time < 12.0 and self.is_running:
            rospy.sleep(0.1)
        
        # Stop movement
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)
        
        rospy.loginfo("Navigation to place completed")
        return True
    
    def place_object(self):
        """Place the grasped object"""
        rospy.loginfo("Placing object...")
        
        try:
            # Open gripper
            hand_msg = robotHandPosition()
            hand_msg.left_hand_position = [0, 0, 0, 0, 0, 0]  # Open left hand
            hand_msg.right_hand_position = [0, 0, 0, 0, 0, 0]  # Open right hand
            
            self.hand_control_pub.publish(hand_msg)
            rospy.sleep(1.0)
            
            rospy.loginfo("Object placed successfully")
            return True
            
        except Exception as e:
            rospy.logerr(f"Place error: {e}")
            return False
    
    def return_home(self):
        """Return to home position"""
        rospy.loginfo("Returning to home position...")
        
        # Simple navigation: return to origin
        cmd_pose = Twist()
        cmd_pose.linear.x = -2.0
        cmd_pose.linear.y = -0.5
        cmd_pose.linear.z = 0.0
        cmd_pose.angular.z = -math.pi/4  # -45 degrees
        
        self.cmd_pose_pub.publish(cmd_pose)
        
        # Wait for navigation to complete
        start_time = time.time()
        while time.time() - start_time < 15.0 and self.is_running:
            rospy.sleep(0.1)
        
        # Stop movement
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)
        
        rospy.loginfo("Return to home completed")
        return True
    
    def get_demo_status(self):
        """Get current demo status"""
        return {
            'state': self.demo_state,
            'is_running': self.is_running,
            'current_pose': self.current_pose,
            'target_pose': self.target_pose
        }
    
    def run(self):
        """Main run loop"""
        rospy.loginfo("Navigation, Detection and Grasp Demo started")
        rospy.loginfo("Press Enter to start the demo...")
        
        # Wait for user input to start
        try:
            input()
            self.start_demo()
        except KeyboardInterrupt:
            rospy.loginfo("Demo interrupted by user")
        except EOFError:
            # Auto-start in non-interactive mode
            rospy.loginfo("Auto-starting demo...")
            self.start_demo()
        
        # Main loop
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            # Check if demo is still running
            if not self.demo_thread.is_alive() and self.is_running:
                self.is_running = False
            
            rate.sleep()

def main():
    try:
        demo = NavDetectGraspDemo()
        demo.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Navigation, Detection and Grasp Demo interrupted")
    except Exception as e:
        rospy.logerr(f"Navigation, Detection and Grasp Demo error: {e}")

if __name__ == '__main__':
    main() 