#!/usr/bin/env python3
"""
使用已登录的 session 调用 get_value_by_xmlnode API - 尝试解密
"""

import requests
import json
import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")
from crypto import AESEncryptor

HOST = "http://192.168.1.1"

session = requests.Session()
session.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://192.168.1.1/main.html",
    "Origin": "http://192.168.1.1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# 先登录
print("获取 session 并登录...")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

body = {
    "dataObj": {"username": "admin", "password": "chr@1998"},
    "ajaxmethod": "DO_WEB_LOGIN",
    "sessionid": sid
}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN", data=encrypted)
print(f"登录: {resp.text}")

# 检查 Cookie
print(f"Cookies: {session.cookies.get_dict()}")

# 获取新 session
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]
print(f"Session ID: {sid}")

# 测试 get_value_by_xmlnode API（加密方式）
api_params = {
    "SerialNumber": "DeviceInfo.SerialNumber",
    "SoftwareVersion": "DeviceInfo.SoftwareVersion", 
    "HardwareVersion": "DeviceInfo.HardwareVersion",
    "Modem5GTemperature": "X_FH_MobileNetwork.Temperature.Modem5GTemperature"
}

# 构造请求数据（和浏览器一样的格式）
request_data = {
    "dataObj": {"url": api_params},
    "sessionid": sid
}

encrypted = AESEncryptor.encrypt(json.dumps(request_data), sid[:16])
resp = session.post(f"{HOST}/api/sign/get_value_by_xmlnode", data=encrypted)

print(f"\n=== get_value_by_xmlnode API ===")
print(f"状态码: {resp.status_code}")
print(f"响应文本: {resp.text}")

# 尝试解密
if resp.text:
    try:
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        print(f"解密后: {decrypted}")
    except Exception as e:
        print(f"解密失败: {e}")

# 尝试其他 API
print("\n\n=== 尝试 get_cmd_result_web ===")
# 获取 uptime
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

request_data = {
    "dataObj": {"key": "UPTIME"},
    "sessionid": sid
}
encrypted = AESEncryptor.encrypt(json.dumps(request_data), sid[:16])
resp = session.post(f"{HOST}/api/sign/get_cmd_result_web", data=encrypted)

print(f"状态码: {resp.status_code}")
print(f"响应文本: {resp.text}")
if resp.text:
    try:
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        print(f"解密后: {decrypted}")
    except Exception as e:
        print(f"解密失败: {e}")
