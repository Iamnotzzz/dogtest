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

int main(int argc, char **argv)
{
  if (argc < 2)
  {
    std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
    exit(-1);
  }
  unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
  // argv[1]由终端传入，为机器人连接的网卡名称

  // 创建sport client对象
  unitree::robot::go2::SportClient sport_client;
  sport_client.SetTimeout(10.0f);  // 设置超时时间为10秒
  sport_client.Init();             // 初始化运动客户端
  sport_client.WaitLeaseApplied(); // 等待租约申请完成
  sport_client.RecoveryStand();    // 恢复机器人站立状态
  sleep(3);

  std::cout << "台阶" << std::endl;
  sport_client.ClassicWalk(true);
  for(int i=0;i<30;i++)
  {
    if(i<15)
    {
      sport_client.Move(0.28, 0, -0.1); // 直行
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    else if(i>=15&&i<20)
    {
      sport_client.Move(0, 0, 0.2); // 左转
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    else if(i>=20&&i<30)
    {
      sport_client.Move(0.28, 0, 0); // 直行
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
  }
  sport_client.ClassicWalk(false);
  sport_client.StopMove();

  return 0;
}