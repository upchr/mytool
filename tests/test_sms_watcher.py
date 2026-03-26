#!/usr/bin/bin/python3
"""测试短信监听器 - 只通知新短信"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from watcher import SMSWatcher

# 创建监听器
watcher = SMSWatcher(
    host="http://192.168.1.1",
    username="admin",
    password="chr@1998",
    notifiers=[],
    check_interval=3.0
)

# 模拟启动流程
print("=== 模拟首次启动 ===")

# 登录
from client import CPEClient
client = CPEClient("http://192.168.1.1")
success, msg = client.login("admin", "chr@1998")
print(f"登录: {msg}")

# 获取短信列表
sms_list = client.get_sms_list()
print(f"短信总数: {len(sms_list)}")

# 记录现有短信 ID
for sms in sms_list:
    if sms.id:
        watcher._processed_sms_ids.add(sms.id)

print(f"已记录 {len(watcher._processed_sms_ids)} 条历史短信 ID")

# 模拟检查新短信
print("\n=== 模拟检查新短信 ===")
new_sms_list = client.get_sms_list()
new_sms = [sms for sms in new_sms_list if sms.id and sms.id not in watcher._processed_sms_ids]
print(f"新短信数量: {len(new_sms)}")

# 如果有新短信，显示
if new_sms:
    for sms in new_sms[:5]:
        print(f"  新短信: {sms.phone} - {sms.content[:30]}...")
else:
    print("  没有新短信（已过滤历史短信）")

client.logout()
print("\n完成")
