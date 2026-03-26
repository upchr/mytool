#!/usr/bin/env python3
"""
测试 CPE API（浏览器后端）
"""

import sys
import json

sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client_browser import CPEClientBrowser
import urllib.request

def send_to_feishu(message: str):
    """发送消息到飞书"""
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

def main():
    print("=" * 60)
    print("CPE API 测试（浏览器后端）")
    print("=" * 60)

    # 创建客户端
    client = CPEClientBrowser("http://192.168.1.1")

    # 登录
    print("\n[Step 1] 登录...")
    success, message = client.login("admin", "chr@1998")
    print(f"  登录结果: {message}")

    if not success:
        print("登录失败，退出")
        return

    try:
        # 获取设备信息
        print("\n[Step 2] 获取设备信息...")
        device_info = client.get_device_info()
        
        print(f"  设备型号: {device_info.model_name}")
        print(f"  MAC 地址: {device_info.mac_address}")
        print(f"  运营商: {device_info.operator_name}")

        # 发送到飞书
        message = f"""【CPE 设备信息（浏览器后端 API）】

✅ API 调用成功！

📋 基本信息：
• 设备型号: {device_info.model_name}
• MAC 地址: {device_info.mac_address}
• 运营商: {device_info.operator_name}
• 区域: {device_info.i18n}

🌐 网络配置：
• LAN IP: {device_info.lan_ip}

---
数据来源: Python + 浏览器自动化 API
"""
        
        send_to_feishu(message)
        print("\n✅ 已发送到飞书")

    finally:
        # 关闭
        print("\n[Step 3] 关闭连接...")
        client.close()
        print("  已关闭")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
