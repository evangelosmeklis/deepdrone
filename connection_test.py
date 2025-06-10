import sys
from dronekit import connect, APIException
import time

# Check if a connection string is provided
if len(sys.argv) < 2:
    print("错误：请提供连接字符串（例如：COM4）")
    sys.exit(1)

connection_string = sys.argv[1]

print(f"正在尝试连接到飞行器：{connection_string}...")

try:
    # 连接到飞行器
    # wait_ready=True 会等待无人机发送心跳和参数。
    # timeout 单位是秒。
    vehicle = connect(connection_string, wait_ready=True, timeout=60)

    print("连接成功！")
    print("\n飞行器属性:")
    print(f"  - GPS 信息: {vehicle.gps_0}")
    print(f"  - 电池: {vehicle.battery}")
    print(f"  - 系统状态: {vehicle.system_status.state}")
    print(f"  - 模式: {vehicle.mode.name}")
    print(f"  - 是否可解锁?: {vehicle.is_armable}")
    print(f"  - 最后心跳: {vehicle.last_heartbeat}")

except APIException as e:
    print(f"连接失败：DroneKit API 错误 - {e}")
    print("请检查以下几点：")
    print("  - 无人机是否已开机并连接到电脑？")
    print("  - COM 端口号是否正确？（可以在 Windows 设备管理器中查看）")
    print("  - 是否安装了正确的驱动程序（例如 SiLabs CP210x）？")

except Exception as e:
    print(f"发生意外错误：{e}")
    print("这可能是由多种问题引起的，包括驱动程序问题或硬件故障。")

finally:
    if 'vehicle' in locals() and vehicle is not None:
        print("\n正在关闭连接。")
        vehicle.close()
    print("测试完成。") 