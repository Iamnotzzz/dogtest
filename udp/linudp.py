import socket
import rospy
from geometry_msgs.msg import Twist


def udp_server():

    rospy.init_node('udp_listener', anonymous=True)


    server_ip = "192.168.1.9"  # 接受所有IP的消息
    server_port = 9990  # 选择与 Windows 端一致的端口号

    # 创建 UDP 套接字
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_ip, server_port))

    # 创建一个 Publisher，用来发布 Twist 
    pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rospy.sleep(1)  

    # 创建一个 Twist 消息对象，用于发布速度
    move_cmd = Twist()

    # 接收并处理 UDP 消息
    while not rospy.is_shutdown():
        data, addr = udp_socket.recvfrom(1024)  
        message = data.decode('utf-8')
        rospy.loginfo(f"Received message: {message} from {addr}")

        # 控制小乌龟的逻辑
        if message == "move_up":
            rospy.loginfo("Moving turtle up...")
            move_cmd.linear.x = 1.0  
            move_cmd.angular.z = 0.0  
        elif message == "move_down":
            rospy.loginfo("Moving turtle down...")
            move_cmd.linear.x = -1.0  
            move_cmd.angular.z = 0.0  
        elif message == "move_left":
            rospy.loginfo("Moving turtle left...")
            move_cmd.linear.x = 0.0  
            move_cmd.angular.z = 1.0  
        elif message == "move_right":
            rospy.loginfo("Moving turtle right...")
            move_cmd.linear.x = 0.0  
            move_cmd.angular.z = -1.0  
        elif message == "stop":
            rospy.loginfo("Stopping turtle...")
            move_cmd.linear.x = 0.0  
            move_cmd.angular.z = 0.0  
        else:
            rospy.logwarn(f"Unknown command: {message}")

        # 发布控制命令
        pub.publish(move_cmd)

    # 关闭套接字
    udp_socket.close()

if __name__ == "__main__":
    try:
        udp_server()
    except rospy.ROSInterruptException:
        pass

