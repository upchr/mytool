#!/usr/bin/env python3
"""
测试更新后的 CPEClient
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
import json
import urllib.request

print("=" * 60)
print("测试 CPEClient（修复后）")
print("=" * 60)

client = CPEClient("http://192.168.1.1")

# 登录
print("\n[Step 1] 登录...")
success, message = client.login("admin", "chr@1998")
print(f"  结果: {message}")

if success:
    # 获取设备信息
    print("\n[Step 2] 获取设备信息...")
    info = client.get_device_info()
    
    print(f"  设备型号: {info.model_name}")
    print(f"  MAC 地址: {info.mac_address}")
    print(f"  运营商: {info.operator_name}")
    
    # 发送到飞书
    message = f"""【CPE 设备信息（CPEClient 修复后）】

✅ 纯 API 调用成功！

📋 基本信息：
• 设备型号: {info.model_name}
• MAC 地址: {info.mac_address}
• 运营商: {info.operator_name}
• 语言: {info.i18n}

---
修复内容：POST 请求需要添加 sessionid 字段
"""
    
    token_resp = urllib.request.urlopen(urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({
            "app_id": "cli_a93b8e2dcc385bd9",
            "app_secret": "ovvVRxM8uJCfAdQZbrrmldXm6rHoeywf"
        }).encode(),
        headers={"Content-Type": "application/json"}
    ))
    token = json.loads(token_resp.read())["tenant_access_token"]
    
    urllib.request.urlopen(urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        data=json.dumps({
            "receive_id": "ou_c3a45bb5120ba945c08b084a38a9d542",
            "msg_type": "text",
            "content": json.dumps({"text": message})
        }).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    ))
    print("\n✅ 已发送到飞书")
    
    # 登出
    client.logout()
    print("\n已登出")

print("\n" + "=" * 60)
