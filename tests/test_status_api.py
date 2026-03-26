#!/usr/bin/env python3
"""
测试加密 API 获取设备状态
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
from crypto import AESEncryptor
import requests
import json

HOST = "http://192.168.1.1"

session = requests.Session()
session.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
})

# 登录
print("登录...")
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

# 测试不同 API
print("\n测试 FHAPIS（加密）API...")
apis = [
    "get_device_status",
    "get_system_info", 
    "get_lan_info",
    "get_wan_info",
    "get_runtime_info",
    "get_temperature"
]

for api in apis:
    resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
    sid = resp.json()["sessionid"]
    
    body = {
        "dataObj": None,
        "ajaxmethod": api,
        "sessionid": sid
    }
    encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
    
    resp = session.post(f"{HOST}/api/tmp/FHAPIS?ajaxmethod={api}", data=encrypted)
    print(f"\n{api}:")
    print(f"  状态码: {resp.status_code}")
    if resp.text:
        try:
            decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
            print(f"  响应: {decrypted[:200]}")
        except:
            print(f"  响应: {resp.text[:200]}")
