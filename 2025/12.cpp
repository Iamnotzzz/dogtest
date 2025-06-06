#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sstream>
#include <thread>
#include <chrono>
#include <unitree/robot/client/client.hpp>
#include <unitree/robot/go2/sport/sport_client.hpp>

int main(int argc, char **argv) {
    // 检查命令行参数是否足够
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }
  
    // 初始化机器人通信接口
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);

    // 创建并初始化运动控制客户端
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f); // 设置超时时间为10秒
    sport_client.Init(); // 初始化运动客户端
    sport_client.WaitLeaseApplied(); // 等待租约申请完成
    sport_client.RecoveryStand(); // 恢复机器人站立状态
    sleep(3); // 等待3秒

    // 创建TCP客户端套接字
    int client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket == -1) {
        std::cerr << "Error: Could not create socket" << std::endl;
        return 1;
    }

    // 配置服务器地址
    sockaddr_in server_address;
    server_address.sin_family = AF_INET; // 使用IPv4协议
    server_address.sin_port = htons(12346); // 设置端口号为12346
    inet_pton(AF_INET, "192.168.123.18", &server_address.sin_addr); // 设置服务器IP地址

    // 尝试连接到服务器
    if (connect(client_socket, (sockaddr*)&server_address, sizeof(server_address)) == -1) {
        std::cerr << "Error: Connection failed" << std::endl;
        close(client_socket);
        return 1;
    }

    // 循环接收服务器发送的消息
    while (true) {
        char buffer[1024]; // 用于存储接收到的数据
        ssize_t bytes_received = recv(client_socket, buffer, 1024, 0); // 接收数据
        if (bytes_received == -1) {
            std::cerr << "Error: Failed to receive data" << std::endl;
        } else if (bytes_received == 0) {
            std::cout << "Connection closed by server" << std::endl;
            break; // 如果服务器关闭连接，退出循环
        } else {
            buffer[bytes_received] = '\0'; // 添加字符串结束符
            std::cout << "收到来自服务器的消息: " << buffer << std::endl;

            // 分割字符串，提取浮点数和ID
            std::istringstream iss(buffer);
            float received_float_1, received_float_2, received_float_3;
            int received_id;
            char delimiter;
            if (!(iss >> received_float_1 >> delimiter >> received_float_2 >> delimiter >> received_float_3 >> delimiter >> received_id)) {
                std::cerr << "Error: Failed to parse message" << std::endl;
            } else {
                // 根据接收到的ID执行不同的动作
                if (received_id == 0) {
                    // ID为0时，判断是否停止运动
                    if (received_float_1 - 0 <= 0.001) {
                        sport_client.StopMove(); // 停止运动
                    } else {
                        // 根据接收到的浮点数调整运动参数
                        sport_client.Move(0.25, 0, (-received_float_1 + 1.57 - 0.035) * 1.07);
                    }
                } else if (received_id == 1) {
                    // ID为1时，执行直行动作
                    for (int i = 0; i < 5; ++i) { // 循环5次，每次0.2秒
                        sport_client.Move(0.28, 0, 0); // 直行
                        std::this_thread::sleep_for(std::chrono::milliseconds(200)); // 延时0.2秒
                    }
                } else if (received_id == 2) {
                    // ID为2时，执行左环岛动作
                    std::cout << "左环岛2" << std::endl;
                    sport_client.Move(0.28, 0, 0.4); // 左转进入左环岛
                } else if (received_id == 3) {
                    // ID为3时，执行右环岛动作
                    std::cout << "右环岛1" << std::endl;
                    for (int i = 0; i < 4; ++i) { // 循环4次，每次0.2秒
                        sport_client.Move(0.28, 0, 0); // 直行
                        std::this_thread::sleep_for(std::chrono::milliseconds(200)); // 延时0.2秒
                    }
                    sport_client.Move(0.18, 0, (-received_float_1 + 1.57 - 0.035) * 1.35); // 调整方向
                } else if (received_id == 4) {
                    // ID为4时，执行右环岛动作
                    std::cout << "右环岛2" << std::endl;
                    sport_client.Move(0.28, 0, 0.68); // 左转直角弯
                }
                else if (received_id == 5) {
                    // ID为5时，执行避障动作
                    std::cout << "避障" << std::endl;
                    sport_client.FreeAvoid(true); // 进入避障模式
                    sport_client.Move(0.18, 0, 0.68); // 左转直角弯
                }
                else if (received_id == 6) {
                    // ID为6时，执行轨迹定位动作
                    time_seg = 0.2; //参考轨迹的时间步长
                    time_temp = ct - time_seg; //当前时刻

                    for (int i = 0; i < 30; i++)

                    {
                        time_temp += time_seg;
                        
                        //以程序运行时的位置为原点，计算一个圆形轨迹的路径点
                        px_local = 0.5 * sin(0.5 * time_temp);
                        py_local = 0.5 * cos(0.5 * time_temp)-1;
                        yaw_local = 0;
                        vx_local = 0.25 * cos(0.5 * time_temp);
                        vy_local = -0.25 * sin(0.5 * time_temp);
                        vyaw_local = 0;
                        
                        //转化为绝对坐标系下的路径点
                        path_point_tmp.timeFromStart = i * time_seg;
                        path_point_tmp.x = px_local * cos(yaw0) - py_local * sin(yaw0) + px0;
                        path_point_tmp.y = px_local * sin(yaw0) + py_local * cos(yaw0) + py0;
                        path_point_tmp.yaw = yaw_local + yaw0;
                        path_point_tmp.vx = vx_local * cos(yaw0) - vy_local * sin(yaw0);
                        path_point_tmp.vy = vx_local * sin(yaw0) + vy_local * cos(yaw0);
                        path_point_tmp.vyaw = vyaw_local;
                        path.push_back(path_point_tmp);
                    }
                    sport_client.TrajectoryFollow(path);
                    
                }
                else if (received_id == 7) {
                    // ID为7时，执行上台阶动作
                    std::cout << "台阶" << std::endl;
                    sport_client.ClassicWalk(true);
                    sport_client.Move(0.28, 0, 0); // 直行 
                }
                
            }
        }
    }
    close(client_socket); // 关闭套接字

    return 0;
}

