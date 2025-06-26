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
#include <unitree/robot/go2/sport/sport_client.hpp>
#include <unistd.h>

//这个是直行函数

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
                    std::cout << "巡线直行" << std::endl;
                    // ID为0时，判断是否停止运动
                    if (received_float_1 - 0 <= 0.001) {
                        sport_client.StopMove(); // 停止运动
                    } else {
                        // 根据接收到的浮点数调整运动参数
                        sport_client.Move(0.25, 0, (-received_float_1 + 1.57 - 0.035) * 1.07);
                    }
                } 
            }
        }
    }
    close(client_socket); // 关闭套接字

    return 0;
}

