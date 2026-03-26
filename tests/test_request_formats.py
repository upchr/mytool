#!/usr/bin/env python3
"""
测试不同的数据格式
"""

import requests
import json
import random
import sys

sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")
from crypto import AESEncryptor

HOST = "http://192.168.1.1"

session = requests.Session()

# 登录
print("登录...")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sessionid = resp.json().get("sessionid", "")
body = {
    "dataObj": {"username": "admin", "password": "chr@1998"},
    "ajaxmethod": "DO_WEB_LOGIN",
    "sessionid": sessionid
}
encrypted = AESEncryptor.encrypt(json.dumps(body), sessionid[:16])
resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN?_test", data=encrypted)
print(f"登录: {resp.text}")

# 测试不同的请求方式
print("\n测试不同的请求方式...")

url = f"{HOST}/api/tmp/FHNCAPIS?_test"
data = {"dataObj": None, "ajaxmethod": "get_device_info"}

# 方式 1: json 参数
print("\n方式 1: json 参数")
resp = session.post(url, json=data)
print(f"  状态码: {resp.status_code}, 响应: {resp.text[:100] if resp.text else '(空)'}")

# 方式 2: data 参数 + Content-Type: application/json
print("\n方式 2: data 参数 + JSON Content-Type")
resp = session.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
print(f"  状态码: {resp.status_code}, 响应: {resp.text[:100] if resp.text else '(空)'}")

# 方式 3: form 表单
print("\n方式 3: form 表单")
resp = session.post(url, data=data)
print(f"  状态码: {resp.status_code}, 响应: {resp.text[:100] if resp.text else '(空)'}")

# 方式 4: GET 请求
print("\n方式 4: GET 请求")
resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_device_info")
print(f"  状态码: {resp.status_code}, 响应: {resp.text[:100] if resp.text else '(空)'}")

# 方式 5: 带完整请求头
print("\n方式 5: 完整请求头")
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=utf-8"
}
resp = session.post(url, data=json.dumps(data), headers=headers)
print(f"  状态码: {resp.status_code}, 响应: {resp.text[:100] if resp.text else '(空)'}")

print("\n完成")
