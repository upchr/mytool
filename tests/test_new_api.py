#!/usr/bin/env python3
"""
测试 CPEClient 新功能
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient

# 创建客户端
client = CPEClient("http://192.168.1.1")

# 登录
print("登录...")
success, msg = client.login("admin", "chr@1998")
print(f"登录结果: {msg}")

if success:
    # 获取设备详细信息
    print("\n" + "=" * 60)
    print("获取设备详细信息")
    print("=" * 60)
    
    details = client.get_device_details()
    print(f"原始数据: {details}")
    
    # 温度
    print("\n--- 温度 ---")
    temp = client.get_temperature()
    print(f"5G 温度: {temp.get('5g', 'N/A')}°C")
    print(f"4G 温度: {temp.get('4g', 'N/A')}°C")
    
    # 系统使用率
    print("\n--- 系统使用率 ---")
    usage = client.get_system_usage()
    print(f"CPU 使用率: {usage.get('cpu', 'N/A')}%")
    print(f"内存使用率: {usage.get('memory', 'N/A'):.2f}%")
    
    # 运行时间
    print("\n--- 运行时间 ---")
    uptime = client.get_uptime()
    print(f"运行时间: {uptime.get('days', 0)}天 {uptime.get('hours', 0)}小时 {uptime.get('minutes', 0)}分钟")
    
    # 登出
    print("\n登出...")
    client.logout()
    print("完成")
