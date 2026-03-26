#!/usr/bin/env python3
"""测试短信监听器 - 启动时通知未读短信"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
from watcher import SMSWatcher

# 创建监听器
watcher = SMSWatcher(
    host="http://192.168.1.1",
    username="admin",
    password="chr@1998",
    notifiers=[],
    check_interval=3.0
)

# 登录
client = CPEClient("http://192.168.1.1")
success, msg = client.login("admin", "chr@1998")
print(f"登录: {msg}")

# 获取短信列表
sms_list = client.get_sms_list()
print(f"短信总数: {len(sms_list)}")

# 找出未读短信
unread_sms = [sms for sms in sms_list if not sms.is_read and not sms.is_sent]
print(f"未读短信: {len(unread_sms)}")

if unread_sms:
    print("\n未读短信列表:")
    for sms in unread_sms[:10]:
        print(f"  [{sms.time}] {sms.phone}: {sms.content[:30]}...")
else:
    print("\n没有未读短信")

client.logout()
print("\n完成")
