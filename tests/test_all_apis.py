#!/usr/bin/env python3
"""
测试所有 CPE API 方法
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
    "Content-Type": "application/json; charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{HOST}/main.html",
    "Origin": HOST
})

def get_sessionid():
    resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
    return resp.json().get("sessionid", "")

def login():
    sid = get_sessionid()
    body = {
        "dataObj": {"username": "admin", "password": "chr@1998"},
        "ajaxmethod": "DO_WEB_LOGIN",
        "sessionid": sid
    }
    encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
    resp = session.post(f"{HOST}/api/sign/DO_WEB_LOGIN", data=encrypted)
    print(f"登录: {resp.text}")

def test_api_fhncapis(method_name):
    """测试 FHNCAPIS（不需要验证）"""
    sid = get_sessionid()
    body = {
        "dataObj": None,
        "ajaxmethod": method_name,
        "sessionid": sid
    }
    encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
    url = f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod={method_name}"
    resp = session.post(url, data=encrypted)
    return resp.status_code, resp.text[:200] if resp.text else "(empty)"

def test_api_fhapis(method_name, data=None):
    """测试 FHAPIS（需要加密）"""
    sid = get_sessionid()
    body = {
        "dataObj": data,
        "ajaxmethod": method_name,
        "sessionid": sid
    }
    encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
    url = f"{HOST}/api/tmp/FHAPIS?_={hash('test')}"
    resp = session.post(url, data=encrypted)
    
    if resp.text.strip():
        try:
            decrypted = AESEncryptor.decrypt(resp.text.strip(), sid[:16])
            return resp.status_code, decrypted[:200]
        except:
            return resp.status_code, resp.text[:200]
    return resp.status_code, "(empty)"

def test_api_get(method_name):
    """测试 GET API"""
    url = f"{HOST}/api/tmp/{method_name}"
    resp = session.get(url)
    return resp.status_code, resp.text[:200] if resp.text else "(empty)"

# 登录
print("=" * 60)
print("登录")
print("=" * 60)
login()

# 测试各种 API
apis_to_test = [
    # FHNCAPIS（不需要验证）
    ("FHNCAPIS", "get_device_info", None),
    ("FHNCAPIS", "get_heartbeat", None),
    ("FHNCAPIS", "is_encrypt", None),
    
    # FHAPIS（需要加密）- 无参数
    ("FHAPIS", "get_signal_info", None),
    ("FHAPIS", "get_network_info", None),
    ("FHAPIS", "get_sms_data", None),
    ("FHAPIS", "get_wifi_info", None),
    ("FHAPIS", "get_station_list", None),
    ("FHAPIS", "get_header_info", None),
    
    # FHAPIS - 有参数
    ("FHAPIS", "get_value_by_xmlnode", {
        "Temperature": "X_FH_MobileNetwork.Temperature.Modem5GTemperature"
    }),
    
    # GET API
    ("GET", "IS_LOGGED_IN", None),
    ("GET", "heartbeat", None),
]

print("\n" + "=" * 60)
print("API 测试结果")
print("=" * 60)

for api_type, method_name, data in apis_to_test:
    try:
        if api_type == "FHNCAPIS":
            status, result = test_api_fhncapis(method_name)
        elif api_type == "FHAPIS":
            status, result = test_api_fhapis(method_name, data)
        else:  # GET
            status, result = test_api_get(method_name)
        
        status_icon = "✅" if status == 200 else "❌"
        print(f"\n{status_icon} {api_type} - {method_name}")
        print(f"   状态码: {status}")
        print(f"   响应: {result}")
    except Exception as e:
        print(f"\n❌ {api_type} - {method_name}")
        print(f"   错误: {e}")
