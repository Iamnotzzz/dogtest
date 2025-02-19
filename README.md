# udp-ros-dogtest

## 这是一个基于 Python 的测试程序，用来测试 UDP 从 Windows 到 Linux 主机的通信。

## 本人使用的虚拟机为wsl，无需在linux中安装vscode，详情请参阅vscode官方帮助文档:https://code.visualstudio.com/docs/remote/wsl

### 在使用之前，应该安装的有：

#### 1. Windows 环境下：

- python3
- pynput（用于读取键盘信息）
- vscode

##### 快速安装链接：

- [Python3 安装](https://www.python.org/downloads/)
- [Pynput 安装](https://pypi.org/project/pynput/)  
  安装命令：  
  ```bash
  pip install pynput
  ```
- [VSCode 安装](https://code.visualstudio.com/Download)

#### 2. Linux 环境下：

- 安装 vscode
- 安装 ROS（请安装 ROS1），并确保可以正确运行 ROS 的检测程序（如小乌龟）。
- 安装 rospy

##### 安装命令：

- 安装 VSCode：  
  ```bash
  sudo apt install code
  ```

- 安装 ROS1（以 Ubuntu 为例）：  
  ```bash
  sudo apt update
  sudo apt install ros-noetic-desktop-full
  ```

- 安装 rospy：  
  ```bash
  sudo apt install python3-rospy
  ```

##### 官方安装指南：
- [ROS1 安装指南](http://wiki.ros.org/ROS/Installation)
- [rospy 安装](http://wiki.ros.org/rospy)

##### 一键安装程序（来自鱼香ros）

```bash
    wget http://fishros.com/install -O fishros && . fishros
```


### 关于ros安装这里建议参阅鱼香 ROS 发布的一键 ROS 安装程序，帮助文档地址为：[https://fishros.com/](https://fishros.com/)