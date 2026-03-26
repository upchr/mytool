#!/usr/bin/env python3
"""
使用 get_value_by_xmlnode API 获取设备详细信息
"""

import sys
sys.path.insert(0, "/root/.openclaw/workspace-main/code/cpe_api")

from client import CPEClient
from crypto import AESEncryptor
import requests
import json

HOST = "http://192.168.1.1"

# XML 路径（从浏览器获取）
XML_PATHS = {
    "SerialNumber": "InternetGatewayDevice.DeviceInfo.SerialNumber",
    "SoftwareVersion": "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
    "HardwareVersion": "InternetGatewayDevice.DeviceInfo.HardwareVersion",
    "UpTime": "InternetGatewayDevice.DeviceInfo.UpTime",
    "CPUTemperature": "InternetGatewayDevice.DeviceInfo.X_FH_CPU.Temperature",
    "ModelName": "InternetGatewayDevice.DeviceInfo.ModelName",
    "Manufacturer": "InternetGatewayDevice.DeviceInfo.Manufacturer",
    "ProductClass": "InternetGatewayDevice.DeviceInfo.ProductClass"
}

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

# 使用 get_value_by_xmlnode API
print("\n获取设备详细信息...")

resp = session.get(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid")
sid = resp.json()["sessionid"]

# 构造请求
data_obj = {}
url_map = {}
for key, path in XML_PATHS.items():
    data_obj[f"get{key}"] = path
    url_map[f"get{key}"] = path

body = {
    "dataObj": {"url": url_map},
    "ajaxmethod": "get_value_by_xmlnode",
    "sessionid": sid
}

encrypted = AESEncryptor.encrypt(json.dumps(body), sid[:16])
resp = session.post(f"{HOST}/api/tmp/FHNCAPIS?ajaxmethod=get_value_by_xmlnode", data=encrypted)

print(f"状态码: {resp.status_code}")
if resp.text:
    try:
        decrypted = AESEncryptor.decrypt(resp.text, sid[:16])
        data = json.loads(decrypted)
        print("\n设备详细信息:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"解密失败: {e}")
