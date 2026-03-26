#!/usr/bin/env python3
"""测试持续监听短信功能"""

import sys
import time
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
from watcher import SMSWatcher

print("=== 测试持续监听 ===")

# 回调函数
received = []
def on_sms(sms):
    received.append(sms)
    print(f"[收到短信] {sms.time} | {sms.phone}: {sms.content[:30]}...")

# 创建监听器
watcher = SMSWatcher(
    host="http://192.168.1.1",
    username="admin",
    password="chr@1998",
    notifiers=[],
    check_interval=3.0,
    on_sms=on_sms
)

# 手动模拟监听循环
print("\n1. 初始化...")
client = CPEClient("http://192.168.1.1")
success, msg = client.login("admin", "chr@1998")
print(f"登录: {msg}")

if success:
    # 获取短信列表
    sms_list = client.get_sms_list()
    print(f"短信总数: {len(sms_list)}")
    
    # 找出未读短信
    unread_sms = [sms for sms in sms_list if not sms.is_read and not sms.is_sent]
    print(f"未读短信: {len(unread_sms)}")
    
    # 记录已处理的短信 ID
    for sms in sms_list:
        if sms.id:
            watcher._processed_sms_ids.add(sms.id)
    print(f"已记录 {len(watcher._processed_sms_ids)} 条短信 ID")
    
    # 模拟持续检查
    print("\n2. 开始持续监听（模拟 3 次检查）...")
    for i in range(3):
        print(f"\n--- 第 {i+1} 次检查 ---")
        
        # 检查登录状态
        logged_in = client.is_logged_in()
        print(f"登录状态: {'已登录' if logged_in else '未登录'}")
        
        # 获取短信列表
        sms_list = client.get_sms_list()
        new_sms = [sms for sms in sms_list if sms.id and sms.id not in watcher._processed_sms_ids]
        
        if new_sms:
            print(f"发现 {len(new_sms)} 条新短信!")
            for sms in new_sms:
                print(f"  [{sms.time}] {sms.phone}: {sms.content[:30]}...")
                watcher._processed_sms_ids.add(sms.id)
        else:
            print("没有新短信")
        
        if i < 2:
            print("等待 3 秒...")
            time.sleep(3)
    
    client.logout()
    print("\n完成")
