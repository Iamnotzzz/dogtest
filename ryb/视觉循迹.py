def advanced_regression(side, y1, y2, y3, y4):
    """最小二乘法拟合直线（示例实现需补充完整）"""
    # 假设已实现返回斜率B和截距A
    global parameterB, parameterA
    # 示例伪代码，需替换为实际计算
    parameterB = 0.5  # 示例斜率
    parameterA = 10  # 示例截距


def run(line_type, start, end, slope, intercept):
    global L_black, R_black, LCenter

    if line_type == 1:  # 左边界
        for i in range(start, end + 1):
            val = int(slope * i + intercept)
            # 边界约束
            L_black[i] = max(0, min(185, val))

    elif line_type == 2:  # 右边界
        for i in range(start, end + 1):
            val = int(slope * i + intercept)
            R_black[i] = max(0, min(185, val))

    elif line_type == 0:  # 中线
        for i in range(start, end + 1):
            # 取左右边界平均值
            val = (L_black[i] // 2) + (R_black[i] // 2)
            LCenter[i] = max(0, min(185, val))


def cross_repair(a, abu, guai, lefty, righty):
    """十字路口补线主逻辑"""
    global flagl, flagr, L_black, R_black, LCenter

    flagl = 0
    flagr = 0

    # 条件判断（加入括号明确优先级）
    if (a >= 4 and ((lefty[0] > 0 and lefty[1] > 0) or (righty[0] > 0 and righty[1] > 0))) or abu >= 3:
        # 左线处理
        if lefty[0] >= 2 and lefty[1] >= 2 and guai == 0:
            advanced_regression(1, lefty[0] - 2, lefty[0], lefty[1], lefty[1] + 2)
            print(f"左斜率 {parameterB} 左截距 {parameterA}")
            run(1, lefty[0], lefty[1], parameterB, parameterA)
            flagl = 1

        # 右线处理
        if righty[0] >= 2 and righty[1] >= 2 and guai == 0:
            advanced_regression(2, righty[0] - 2, righty[0], righty[1], righty[1] + 2)
            print(f"右斜率 {parameterB} 右截距 {parameterA}")
            run(2, righty[0], righty[1], parameterB, parameterA)
            flagr = 1

        # 中线生成逻辑
        if (flagr or flagl) and guai == 0:
            if flagl and not flagr:
                run(0, lefty[0], lefty[1], parameterB, parameterA)
                print(f"入十字前拉线 {a}")
                if abu >= 3:
                    run(0, 0, lefty[0], parameterB, parameterA)
                    run(0, lefty[1], 50, parameterB, parameterA)
            else:
                run(0, righty[0], righty[1], parameterB, parameterA)
                print(f"入十字前拉线 {a}")
                if abu >= 3:
                    run(0, 0, righty[0], parameterB, parameterA)
                    run(0, righty[1], 50, parameterB, parameterA)


# 全局变量初始化示例
L_black = [185] * 100  # 左边界数组
R_black = [0] * 100  # 右边界数组
LCenter = [0] * 100  # 中线数组
parameterB = 0  # 斜率
parameterA = 0  # 截距

# 使用示例
if __name__ == "__main__":
    # 模拟输入参数
    left_points = [10, 30]  # lefty数组
    right_points = [15, 35]  # righty数组

    cross_repair(
        a=5,
        abu=0,
        guai=0,
        lefty=left_points,
        righty=right_points
    )