#!/usr/bin/env python3
"""测试短信功能"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient

client = CPEClient("http://192.168.1.1")

# 登录
print("登录...")
success, msg = client.login("admin", "chr@1998")
print(f"登录结果: {msg}")

if success:
    # 测试短信相关方法
    print("\n=== 测试短信功能 ===")
    
    # 1. 检查新短信（GET 请求）
    has_new = client.get_new_sms_flag()
    print(f"有新短信: {has_new}")
    
    # 2. 获取短信列表
    sms_list = client.get_sms_list()
    print(f"短信总数: {len(sms_list)}")
    
    # 3. 获取未读短信
    unread = client.get_unread_sms()
    print(f"未读短信: {len(unread)}")
    
    if sms_list:
        print(f"\n最新短信:")
        print(f"  时间: {sms_list[0].time}")
        print(f"  号码: {sms_list[0].phone}")
        print(f"  内容: {sms_list[0].content[:50]}...")
        print(f"  已读: {sms_list[0].is_read}")
    
    # 登出
    client.logout()
    print("\n完成")
