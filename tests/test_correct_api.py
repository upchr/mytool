#!/usr/bin/env python3
"""
CPE API 正确调用方式（POST 请求需要加密）
"""

import requests
import json
import random

sys_path = "/root/.openclaw/workspace-main/code/cpe_api"
import sys
sys.path.insert(0, sys_path)
from crypto import AESEncryptor

HOST = "http://192.168.1.1"

print("=" * 60)
print("CPE API 正确调用方式")
print("=" * 60)

session = requests.Session()

# 设置请求头
session.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
})

# Step 1: 获取 sessionid
print("\n[Step 1] 获取 sessionid...")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid&_={random.random()}")
sessionid = resp.json().get("sessionid", "")
print(f"  sessionid: {sessionid}")

# Step 2: 登录
print("\n[Step 2] 登录...")
login_sid_resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid&_={random.random()}")
login_sid = login_sid_resp.json().get("sessionid", "")

body = {
    "dataObj": {"username": "admin", "password": "chr@1998"},
    "ajaxmethod": "DO_WEB_LOGIN",
    "sessionid": login_sid
}
encrypted = AESEncryptor.encrypt(json.dumps(body), login_sid[:16])

resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN?_{random.random()}", data=encrypted, headers={
    "Content-Type": "application/json"
})
print(f"  登录响应: {resp.text}")

# Step 3: 获取设备信息（正确方式）
print("\n[Step 3] 获取设备信息（添加 sessionid + 加密）...")

# 获取新的 sessionid
sid_resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid&_={random.random()}")
sid = sid_resp.json().get("sessionid", "")

# 构造请求数据（添加 sessionid）
body = {
    "dataObj": None,
    "ajaxmethod": "get_device_info",
    "sessionid": sid  # 关键：添加 sessionid
}

# 加密
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])

# 发送
resp = session.post(f"{HOST}/api/tmp/FHNCAPIS?_{random.random()}", data=encrypted, headers={
    "Content-Type": "application/json"
})

print(f"  状态码: {resp.status_code}")
print(f"  响应长度: {len(resp.text)}")

if resp.text and len(resp.text) > 10:
    try:
        # 解密响应
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        data = json.loads(decrypted)
        
        print("\n✅ 成功获取设备信息！")
        print(f"  设备型号: {data.get('model_name')}")
        print(f"  MAC 地址: {data.get('brmac')}")
        
        # 发送到飞书
        import urllib.request
        
        message = f"""【CPE 设备信息（纯 API 成功）】

✅ POST 请求成功！

📋 基本信息：
• 设备型号: {data.get('model_name')}
• MAC 地址: {data.get('brmac')}
• 运营商: {data.get('operator_name')}
• 区域: {data.get('area_code')}

---
数据来源: Python 纯 API（正确加密流程）
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
        
    except Exception as e:
        print(f"  解密失败: {e}")
else:
    print("  响应为空")

print("\n" + "=" * 60)
