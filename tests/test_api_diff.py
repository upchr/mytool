#!/usr/bin/env python3
"""测试 get_device_info API"""

import requests
import json
import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")
from crypto import AESEncryptor

HOST = "http://192.168.1.1"

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json; charset=utf-8",
})

# 登录
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

body = {"dataObj": {"username": "admin", "password": "chr@1998"}, "ajaxmethod": "DO_WEB_LOGIN", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN", data=encrypted)
print(f"登录: {resp.text}")

# 测试 FHNCAPIS
print("\n=== FHNCAPIS ===")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

body = {"dataObj": None, "ajaxmethod": "get_device_info", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_device_info", data=encrypted)
print(f"状态码: {resp.status_code}")
if resp.text:
    decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
    print(f"响应: {decrypted}")

# 测试 FHAPIS
print("\n=== FHAPIS ===")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

body = {"dataObj": None, "ajaxmethod": "get_device_info", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/tmp/FHAPIS?_=test", data=encrypted)
print(f"状态码: {resp.status_code}")
if resp.text:
    try:
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        print(f"响应: {decrypted}")
    except:
        print(f"响应: {resp.text[:100]}")
