#!/usr/bin/env python3
"""
使用已登录的 session 调用 get_value_by_xmlnode API
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
    "Origin": "http://192.168.1.1"
})

# 先获取 session ID 并登录
print("获取 session...")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid_data = resp.json()
sid = sid_data["sessionid"]
print(f"Session ID: {sid}")

# 登录
from crypto import AESEncryptor
body = {
    "dataObj": {"username": "admin", "password": "chr@1998"},
    "ajaxmethod": "DO_WEB_LOGIN",
    "sessionid": sid
}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN", data=encrypted)
print(f"登录: {resp.text}")

# 检查登录后的 cookie
print(f"\nCookie: {session.cookies.get_dict()}")

# 尝试调用 get_value_by_xmlnode API（不加密）
api_params = {
    "SerialNumber": "DeviceInfo.SerialNumber",
    "SoftwareVersion": "DeviceInfo.SoftwareVersion", 
    "HardwareVersion": "DeviceInfo.HardwareVersion",
    "Modem5GTemperature": "X_FH_MobileNetwork.Temperature.Modem5GTemperature"
}

# 先获取新的 session（登录后）
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]
print(f"\n新 Session ID: {sid}")

# 使用 tmp API（不加密）
data = {
    "ajaxmethod": "get_value_by_xmlnode",
    "sessionid": sid,
    "dataObj": json.dumps({"url": api_params})
}

resp = session.post(f"{HOST}/api/tmp/FHNCAPIS", data=data)
print(f"\n/tmp API 响应:")
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text[:500] if len(resp.text) > 500 else resp.text}")

# 尝试 sign API（加密）
encrypted = AESEncryptor.encrypt(json.dumps({
    "ajaxmethod": "get_value_by_xmlnode",
    "sessionid": sid,
    "dataObj": {"url": api_params}
}), sid[:16])

resp = session.post(f"{HOST}/api/sign/get_value_by_xmlnode", data=encrypted)
print(f"\n/sign API 响应:")
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text[:500] if len(resp.text) > 500 else resp.text}")
