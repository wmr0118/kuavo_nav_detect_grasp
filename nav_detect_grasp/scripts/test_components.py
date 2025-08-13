#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Component Test Script for nav_detect_grasp demo
Tests each component to ensure they are working correctly
"""

import rospy
import time
import sys
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import Image, JointState
from kuavo_msgs.msg import armTargetPoses, robotHandPosition
from kuavo_msgs.srv import changeArmCtrlMode, changeArmCtrlModeRequest
from apriltag_ros.msg import AprilTagDetectionArray
from kuavo_msgs.msg import yoloDetection, yoloOutputData

class ComponentTester:
    def __init__(self):
        rospy.init_node('component_tester', anonymous=True)
        
        # 测试结果
        self.test_results = {}
        
        # 测试超时时间
        self.timeout = 5.0
        
        print("=" * 60)
        print("  Navigation, Detection and Grasp Demo - Component Test")
        print("=" * 60)
        print()
    
    def test_ros_master(self):
        """测试ROS Master连接"""
        print("1. 测试ROS Master连接...")
        try:
            rospy.wait_for_service('/rosout', timeout=self.timeout)
            self.test_results['ros_master'] = True
            print("   ✓ ROS Master连接正常")
        except rospy.ROSException:
            self.test_results['ros_master'] = False
            print("   ✗ ROS Master连接失败")
    
    def test_kuavo_msgs(self):
        """测试Kuavo消息包"""
        print("2. 测试Kuavo消息包...")
        try:
            # 测试消息导入
            test_msg = armTargetPoses()
            test_msg.times = [1.0]
            test_msg.values = [0.0] * 14
            
            self.test_results['kuavo_msgs'] = True
            print("   ✓ Kuavo消息包正常")
        except Exception as e:
            self.test_results['kuavo_msgs'] = False
            print(f"   ✗ Kuavo消息包异常: {e}")
    
    def test_apriltag_detection(self):
        """测试AprilTag检测"""
        print("3. 测试AprilTag检测...")
        try:
            # 等待AprilTag检测话题
            msg = rospy.wait_for_message("/robot_tag_info", AprilTagDetectionArray, timeout=self.timeout)
            self.test_results['apriltag_detection'] = True
            print(f"   ✓ AprilTag检测正常，检测到 {len(msg.detections)} 个标签")
        except rospy.ROSException:
            self.test_results['apriltag_detection'] = False
            print("   ✗ AprilTag检测失败或未启动")
    
    def test_camera_stream(self):
        """测试相机流"""
        print("4. 测试相机流...")
        try:
            # 等待相机图像话题
            msg = rospy.wait_for_message("/camera/color/image_raw", Image, timeout=self.timeout)
            self.test_results['camera_stream'] = True
            print(f"   ✓ 相机流正常，图像尺寸: {msg.width}x{msg.height}")
        except rospy.ROSException:
            self.test_results['camera_stream'] = False
            print("   ✗ 相机流失败或未启动")
    
    def test_robot_control(self):
        """测试机器人控制"""
        print("5. 测试机器人控制...")
        try:
            # 测试手臂控制模式切换服务
            rospy.wait_for_service('/arm_traj_change_mode', timeout=self.timeout)
            self.test_results['robot_control'] = True
            print("   ✓ 机器人控制服务正常")
        except rospy.ROSException:
            self.test_results['robot_control'] = False
            print("   ✗ 机器人控制服务失败或未启动")
    
    def test_navigation(self):
        """测试导航功能"""
        print("6. 测试导航功能...")
        try:
            # 测试里程计话题
            msg = rospy.wait_for_message("/odom", rospy.AnyMsg, timeout=self.timeout)
            self.test_results['navigation'] = True
            print("   ✓ 导航功能正常")
        except rospy.ROSException:
            self.test_results['navigation'] = False
            print("   ✗ 导航功能失败或未启动")
    
    def test_yolo_detection(self):
        """测试YOLO检测"""
        print("7. 测试YOLO检测...")
        try:
            # 等待YOLO检测话题
            msg = rospy.wait_for_message("/yolo_detections", yoloOutputData, timeout=self.timeout)
            self.test_results['yolo_detection'] = True
            print(f"   ✓ YOLO检测正常，检测到 {len(msg.detections)} 个目标")
        except rospy.ROSException:
            self.test_results['yolo_detection'] = False
            print("   ✗ YOLO检测失败或未启动")
    
    def test_tf_transforms(self):
        """测试TF变换"""
        print("8. 测试TF变换...")
        try:
            import tf2_ros
            import tf2_geometry_msgs
            
            # 创建TF监听器
            tf_buffer = tf2_ros.Buffer()
            tf_listener = tf2_ros.TransformListener(tf_buffer)
            
            # 等待TF树建立
            time.sleep(1.0)
            
            # 检查关键变换
            transforms = ['base_link', 'camera_link', 'map']
            available_transforms = []
            
            for transform in transforms:
                try:
                    tf_buffer.lookup_transform('base_link', transform, rospy.Time(0), rospy.Duration(0.1))
                    available_transforms.append(transform)
                except:
                    pass
            
            if len(available_transforms) > 0:
                self.test_results['tf_transforms'] = True
                print(f"   ✓ TF变换正常，可用变换: {available_transforms}")
            else:
                self.test_results['tf_transforms'] = False
                print("   ✗ TF变换失败")
                
        except ImportError:
            self.test_results['tf_transforms'] = False
            print("   ✗ TF2包未安装")
        except Exception as e:
            self.test_results['tf_transforms'] = False
            print(f"   ✗ TF变换异常: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始运行组件测试...")
        print()
        
        # 执行测试
        self.test_ros_master()
        self.test_kuavo_msgs()
        self.test_apriltag_detection()
        self.test_camera_stream()
        self.test_robot_control()
        self.test_navigation()
        self.test_yolo_detection()
        self.test_tf_transforms()
        
        print()
        print("=" * 60)
        print("  测试结果汇总")
        print("=" * 60)
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name:20s}: {status}")
        
        print()
        print(f"总计: {total_tests} 项测试")
        print(f"通过: {passed_tests} 项")
        print(f"失败: {failed_tests} 项")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！系统准备就绪。")
            return True
        else:
            print(f"\n⚠️  有 {failed_tests} 项测试失败，请检查相关组件。")
            return False
    
    def print_recommendations(self):
        """打印建议"""
        print("\n" + "=" * 60)
        print("  故障排除建议")
        print("=" * 60)
        
        if not self.test_results.get('ros_master', False):
            print("• ROS Master连接失败:")
            print("  - 检查ROS是否已启动: roscore")
            print("  - 检查网络连接")
        
        if not self.test_results.get('kuavo_msgs', False):
            print("• Kuavo消息包异常:")
            print("  - 检查kuavo_msgs包是否已编译")
            print("  - 运行: catkin_make")
        
        if not self.test_results.get('apriltag_detection', False):
            print("• AprilTag检测失败:")
            print("  - 启动AprilTag检测: roslaunch apriltag_ros continuous_detection.launch")
            print("  - 检查相机是否正常工作")
        
        if not self.test_results.get('camera_stream', False):
            print("• 相机流失败:")
            print("  - 启动相机驱动: roslaunch realsense2_camera rs_camera.launch")
            print("  - 检查相机连接")
        
        if not self.test_results.get('robot_control', False):
            print("• 机器人控制失败:")
            print("  - 启动机器人控制节点")
            print("  - 检查机器人硬件连接")
        
        if not self.test_results.get('navigation', False):
            print("• 导航功能失败:")
            print("  - 启动导航节点")
            print("  - 检查里程计话题")
        
        if not self.test_results.get('yolo_detection', False):
            print("• YOLO检测失败:")
            print("  - 启动YOLO检测节点")
            print("  - 检查YOLO模型文件")
        
        if not self.test_results.get('tf_transforms', False):
            print("• TF变换失败:")
            print("  - 启动TF发布节点")
            print("  - 检查机器人描述文件")

def main():
    try:
        tester = ComponentTester()
        success = tester.run_all_tests()
        
        if not success:
            tester.print_recommendations()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 