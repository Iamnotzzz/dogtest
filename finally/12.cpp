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
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }
  
    // 初始化接口
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);

    // 实例化 sport_client 并初始化
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f); // 超时时间
    sport_client.Init();
    sport_client.WaitLeaseApplied();
    sport_client.RecoveryStand(); // 恢复站立
    sleep(3);

    int client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket == -1) {
        std::cerr << "Error: Could not create socket" << std::endl;
        return 1;
    }

    sockaddr_in server_address;
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(12346); // 端口号12345
    inet_pton(AF_INET, "192.168.123.18", &server_address.sin_addr); // 替换为远程主机的IP地址

    if (connect(client_socket, (sockaddr*)&server_address, sizeof(server_address)) == -1) {
        std::cerr << "Error: Connection failed" << std::endl;
        close(client_socket);
        return 1;
    }

    while (true) {
        char buffer[1024];
        ssize_t bytes_received = recv(client_socket, buffer, 1024, 0);
        if (bytes_received == -1) {
            std::cerr << "Error: Failed to receive data" << std::endl;
        } else if (bytes_received == 0) {
            std::cout << "Connection closed by server" << std::endl;
            break; // 如果服务器关闭了连接，退出循环
        } else {
            buffer[bytes_received] = '\0';
            std::cout << "收到来自服务器的消息: " << buffer << std::endl;

            // 分割字符串，提取浮点数
            std::istringstream iss(buffer);
            float received_float_1, received_float_2, received_float_3;
            int received_id;
            char delimiter;
            if (!(iss >> received_float_1 >> delimiter >> received_float_2 >> delimiter >> received_float_3 >> delimiter >> received_id)) {
                std::cerr << "Error: Failed to parse message" << std::endl;
            } else {
                // 直接调用函数处理接收到的三个浮点数和ID
                if (received_id == 0) {
                    if (received_float_1 - 0 <= 0.001) {
                        sport_client.StopMove();
                    } else {
                        sport_client.Move(0.25, 0, (-received_float_1 + 1.57 - 0.035) * 1.07);
                        // sport_client.Move(0, 0, (-received_float_1 + 1.57 - 0.035) * 0);
                    }
                } else if (received_id == 1) {
                    for (int i = 0; i < 5; ++i) { // 循环5次，每次0.2秒
                        sport_client.Move(0.28, 0, 0); // 直行1s
                        std::this_thread::sleep_for(std::chrono::milliseconds(200)); // 延时0.5秒
                        // 左拐一定路程进入左环岛
                        // for (int i = 0; i < 5; ++i) { // 循环5次，每次0.2秒
                        // sport_client.Move(0.28, 0, (-received_float_1 + 1.57 - 0.035) * 1.1);
                        // std::this_thread::sleep_for(std::chrono::milliseconds(200));
                        // }
                    }
                } else if (received_id == 2) {
                    std::cout << "左环岛2" << std::endl;
                    sport_client.Move(0.28, 0, 0.4); // 这里要左拐，进左环岛1
                } else if (received_id == 3) {
                    std::cout << "右环岛1" << std::endl;
                    for (int i = 0; i < 4; ++i) { // 循环5次，每次0.2秒
                        sport_client.Move(0.28, 0, 0); // 直行1s
                        std::this_thread::sleep_for(std::chrono::milliseconds(200));
                        } 
                        sport_client.Move(0.18, 0, (-received_float_1 + 1.57 - 0.035) * 1.35);
                        // 延时0.5秒
                } else if (received_id == 4) {
                    std::cout << "右环岛2" << std::endl;
                    sport_client.Move(0.28, 0, 0.68); // 直接左拐直角弯，靠后测试
                }
            }
        }
    }
    close(client_socket);

    return 0;
}
// received_float_1-1.57

