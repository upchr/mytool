#!/usr/bin/env python3
"""
测试重构后的 CPEClient
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient

# 创建客户端
client = CPEClient("http://192.168.1.1")

# 登录
print("=" * 60)
print("登录")
print("=" * 60)
success, msg = client.login("admin", "chr@1998")
print(f"登录结果: {msg}")

if success:
    # 1. 设备信息
    print("\n" + "=" * 60)
    print("1. 设备基本信息")
    print("=" * 60)
    info = client.get_device_info()
    print(f"设备型号: {info.model_name}")
    print(f"MAC 地址: {info.mac_address}")
    
    # 2. 设备详细信息
    print("\n" + "=" * 60)
    print("2. 设备详细信息")
    print("=" * 60)
    temp = client.get_temperature()
    print(f"5G 温度: {temp.get('5g', 'N/A')}°C")
    print(f"4G 温度: {temp.get('4g', 'N/A')}°C")
    
    usage = client.get_system_usage()
    print(f"CPU 使用率: {usage.get('cpu', 'N/A')}%")
    print(f"内存使用率: {usage.get('memory', 'N/A'):.2f}%")
    
    uptime = client.get_uptime()
    print(f"运行时间: {uptime.get('days', 0)}天 {uptime.get('hours', 0)}小时 {uptime.get('minutes', 0)}分钟")
    
    # 3. SIM 卡信息
    print("\n" + "=" * 60)
    print("3. SIM 卡信息")
    print("=" * 60)
    sim = client.get_sim_info()
    print(f"IMEI: {sim.get('IMEI', 'N/A')}")
    print(f"IMSI: {sim.get('IMSI', 'N/A')}")
    print(f"运营商: {sim.get('CarrierName', 'N/A')}")
    
    network_mode = sim.get('NetworkMode', '')
    mode_map = {'1': '3G', '2': '4G', '3': '5G'}
    print(f"网络模式: {mode_map.get(network_mode, network_mode)}")
    
    # 4. 信号信息
    print("\n" + "=" * 60)
    print("4. 信号信息")
    print("=" * 60)
    signal = client.get_signal_info()
    print(f"RSRP: {signal.get('RSRP', 'N/A')} dBm")
    print(f"RSSI: {signal.get('RSSI', 'N/A')} dBm")
    print(f"SINR: {signal.get('SINR', 'N/A')} dB")
    print(f"频段: {signal.get('BAND', 'N/A')}")
    print(f"PCI: {signal.get('PCI', 'N/A')}")
    
    # 5G 信号
    ssb_rsrp = signal.get('SSB_RSRP')
    if ssb_rsrp:
        print(f"5G SSB RSRP: {ssb_rsrp} dBm")
    
    # 5. 流量统计
    print("\n" + "=" * 60)
    print("5. 流量统计")
    print("=" * 60)
    traffic = client.get_traffic_stats()
    
    today_tx = traffic.get('TodayTotalTxBytes')
    today_rx = traffic.get('TodayTotalRxBytes')
    if today_tx and today_rx:
        print(f"今日发送: {int(today_tx) / 1024 / 1024:.2f} MB")
        print(f"今日接收: {int(today_rx) / 1024 / 1024:.2f} MB")
    
    # 6. 短信
    print("\n" + "=" * 60)
    print("6. 短信")
    print("=" * 60)
    sms_list = client.get_sms_list()
    print(f"短信总数: {len(sms_list)}")
    if sms_list:
        print(f"最新短信: {sms_list[0].content[:30]}...")
    
    # 7. 心跳检测
    print("\n" + "=" * 60)
    print("7. 心跳检测")
    print("=" * 60)
    print(f"心跳: {'正常' if client.heartbeat() else '失败'}")
    print(f"登录状态: {'已登录' if client.is_logged_in() else '未登录'}")
    
    # 登出
    print("\n" + "=" * 60)
    print("登出")
    print("=" * 60)
    client.logout()
    print("完成")
