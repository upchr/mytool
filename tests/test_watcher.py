#!/usr/bin/env python3
"""测试短信转发功能"""

import sys
import time
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
from watcher import SMSWatcher, FeishuWebhookNotifier

# 加载配置
import os
try:
    from dotenv import load_dotenv
    load_dotenv("/root/.openclaw/workspace-main/code/cpe_api/.env")
except:
    pass

# 创建客户端
client = CPEClient("http://192.168.1.1")

print("登录...")
success, msg = client.login("admin", "chr@1998")
print(f"登录结果: {msg}")

if success:
    # 测试短信列表
    print("\n=== 测试短信列表 ===")
    sms_list = client.get_sms_list()
    print(f"短信总数: {len(sms_list)}")
    
    # 测试监听器（不发送通知）
    print("\n=== 测试监听器 ===")
    
    # 回调函数
    received_sms = []
    def on_sms(sms):
        received_sms.append(sms)
        print(f"收到短信: {sms.phone} - {sms.content[:30]}...")
    
    # 创建监听器
    watcher = SMSWatcher(
        host="http://192.168.1.1",
        username="admin",
        password="chr@1998",
        notifiers=[],  # 不发送通知
        check_interval=3.0,
        on_sms=on_sms
    )
    
    # 手动运行一次检查
    print("\n运行一次检查...")
    sms_list = client.get_sms_list()
    new_sms = [sms for sms in sms_list if sms.id and sms.id not in watcher._processed_sms_ids]
    print(f"新短信数量: {len(new_sms)}")
    
    if new_sms:
        print(f"最新短信: {new_sms[0].phone} - {new_sms[0].content[:50]}...")
    
    # 登出
    client.logout()
    print("\n完成")