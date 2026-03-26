#!/usr/bin/env python3
"""测试 get_new_sms API"""

import requests
import json
import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")
from crypto import AESEncryptor

HOST = "http://192.168.1.1"

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

# 登录
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]
body = {"dataObj": {"username": "admin", "password": "chr@1998"}, "ajaxmethod": "DO_WEB_LOGIN", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN", data=encrypted)
print(f"登录: {resp.text}")

# 测试 get_new_sms API
print("\n=== 测试 get_new_sms ===")

# GET 方式
print("GET 方式:")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_new_sms")
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text}")

# POST 方式（加密）
print("\nPOST 加密方式:")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]
body = {"dataObj": None, "ajaxmethod": "get_new_sms", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_new_sms", data=encrypted)
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text}")

# FHAPIS
print("\nFHAPIS 方式:")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]
body = {"dataObj": None, "ajaxmethod": "get_new_sms", "sessionid": sid}
encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/tmp/FHAPIS?_=test", data=encrypted)
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text}")
if resp.text:
    try:
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        print(f"解密: {decrypted}")
    except:
        pass
