#!/usr/bin/env python3
"""测试格式化设备信息"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient

client = CPEClient("http://192.168.1.1")

print("登录...")
success, msg = client.login("admin", "chr@1998")
print(f"登录结果: {msg}\n")

if success:
    # 获取格式化的设备信息
    info = client.get_device_info_formatted()
    print(info)
    
    client.logout()
