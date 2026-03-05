# app/modules/acme/dns_providers/tencent.py
import logging
import os
import hashlib
import hmac
import json
from datetime import datetime
from typing import Tuple, Optional
import httpx
import time

from app.modules.acme.dns_providers import DnsProvider

logger = logging.getLogger(__name__)

class TencentDnsProvider(DnsProvider):
    def __init__(self, secret_id: str, secret_key: str):
        # 从环境变量读取密钥
        super().__init__(secret_id, secret_key)
        # self.secret_id = os.getenv("TENCENT_SECRET_ID")
        # self.secret_key = os.getenv("TENCENT_SECRET_KEY")

        if not self.secret_id or not self.secret_key:
            raise ValueError("请设置 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")

        self.host = "dnspod.tencentcloudapi.com"
        self.service = "dnspod"
        self.version = "2021-03-23"
        self.algorithm = "TC3-HMAC-SHA256"

        # 创建 HTTPX 客户端
        self.client = httpx.Client(timeout=30.0)

    def _sign(self, key: bytes, msg: str) -> bytes:
        """HMAC-SHA256 签名"""
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _build_authorization(self, action: str, params: dict, timestamp: int) -> Tuple[str, str]:
        """
        构建腾讯云 API v3 签名

        Args:
            action: API 动作名称
            params: 请求参数
            timestamp: 时间戳

        Returns:
            (authorization, payload) - 授权头和请求体
        """
        # 获取日期
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        # 将参数转换为 JSON 字符串（无空格）
        payload = json.dumps(params, separators=(',', ':'), ensure_ascii=False)

        # ************* 步骤 1：拼接规范请求串 *************
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"

        # 注意：x-tc-action 必须是小写
        canonical_headers = (
            f"content-type:{ct}\n"
            f"host:{self.host}\n"
            f"x-tc-action:{action.lower()}\n"
        )
        signed_headers = "content-type;host;x-tc-action"

        # 计算 payload 的哈希值
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest().lower()

        canonical_request = (
            f"{http_request_method}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_request_payload}"
        )

        # ************* 步骤 2：拼接待签名字符串 *************
        credential_scope = f"{date}/{self.service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest().lower()

        string_to_sign = (
            f"{self.algorithm}\n"
            f"{timestamp}\n"
            f"{credential_scope}\n"
            f"{hashed_canonical_request}"
        )

        # ************* 步骤 3：计算签名 *************
        # 派生签名密钥
        secret_date = self._sign(f"TC3{self.secret_key}".encode("utf-8"), date)
        secret_service = self._sign(secret_date, self.service)
        secret_signing = self._sign(secret_service, "tc3_request")

        # 计算最终签名
        signature = hmac.new(
            secret_signing,
            string_to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest().lower()

        # ************* 步骤 4：拼接 Authorization *************
        authorization = (
            f"{self.algorithm} "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return authorization, payload

    def _send_request(self, action: str, params: dict) -> Optional[dict]:
        """发送请求到腾讯云 API"""
        timestamp = int(time.time())

        try:
            # 构建签名和请求体
            authorization, payload = self._build_authorization(action, params, timestamp)

            # 构建请求头
            headers = {
                "Authorization": authorization,
                "Content-Type": "application/json; charset=utf-8",
                "Host": self.host,
                "X-TC-Action": action,
                "X-TC-Timestamp": str(timestamp),
                "X-TC-Version": self.version
            }

            # 打印调试信息
            logger.debug(f"\n=== 调试信息 ===")
            logger.debug(f"Action: {action}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Authorization: {authorization[:100]}...")
            logger.debug(f"Timestamp: {timestamp}")
            logger.debug(f"Date: {datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')}")

            # 发送请求
            response = self.client.post(
                f"https://{self.host}",
                headers=headers,
                content=payload,  # 使用 content 而不是 json，因为我们已经有序列化的 JSON
                timeout=30.0
            )

            # 打印响应
            logger.debug(f"Response Status: {response.status_code}")
            logger.debug(f"Response Body: {response.text[:200]}")

            response.raise_for_status()
            result = response.json()

            # 检查 API 错误
            if "Response" in result and "Error" in result["Response"]:
                error = result["Response"]["Error"]
                logger.error(f"❌ API 错误: {error.get('Code')} - {error.get('Message')}")
                return result

            return result

        except httpx.RequestError as e:
            logger.error(f"❌ 请求错误: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP 错误: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ 未知错误: {e}")
            return None

    def add_txt_record(self, domain: str, subDomain: str, value: str,remark: str='申请证书使用') -> Optional[str]:
        """添加 TXT 记录"""
        action = "CreateRecord"
        params = {
            "Domain": domain,
            "SubDomain": subDomain,
            "RecordType": "TXT",
            "RecordLine": "默认",
            "Value": value,
            "Remark": remark,
            "TTL": 600,
        }

        result = self._send_request(action, params)

        if result and "Response" in result:
            if "Error" in result["Response"]:
                logger.error(f"❌ 添加失败: {result['Response']['Error']['Message']}")
                return None

            record_id = result["Response"].get("RecordId")
            if record_id:
                logger.info(f"✅ 添加 TXT 记录成功, 记录ID: {record_id}")
                return str(record_id)
            else:
                logger.error(f"❌ 添加失败: 未返回 RecordId")
                return None
        else:
            logger.error(f"❌ 添加失败: 无效响应")
            return None

    def del_txt_record(self, domain: str, record_id: str) -> bool:
        """删除 TXT 记录"""
        action = "DeleteRecord"
        params = {
            "Domain": domain,
            "RecordId": int(record_id)  # 确保是整数
        }

        result = self._send_request(action, params)

        if result and "Response" in result:
            if "Error" in result["Response"]:
                logger.error(f"❌ 删除失败: {result['Response']['Error']['Message']}")
                return False
            logger.info(f"✅ 删除 TXT 记录成功, ID: {record_id}")
            return True
        else:
            logger.error(f"❌ 删除失败")
            return False

    def get_record_info(self, domain: str, record_id: str) -> Optional[dict]:
        """获取记录信息"""
        action = "DescribeRecord"
        params = {
            "Domain": domain,
            "RecordId": int(record_id)
        }

        result = self._send_request(action, params)

        if result and "Response" in result:
            if "Error" in result["Response"]:
                logger.error(f"❌ 获取失败: {result['Response']['Error']['Message']}")
                return None
            logger.info(f"✅ 获取记录成功")
            return result
        else:
            logger.error(f"❌ 获取失败")
            return None


# 使用示例
if __name__ == "__main__":
    import time

    from app.core.log.log import setup_logging
    from app.core.config import get_config

    # todo log载入
    config_obj = get_config()
    setup_logging(config_obj)

    logger.debug("=== 腾讯云 DNS 提供者测试 ===")

    # 创建实例
    secret_id = os.getenv("TENCENT_SECRET_ID")
    secret_key = os.getenv("TENCENT_SECRET_KEY")
    provider = TencentDnsProvider(secret_id,secret_key)

    # 测试添加记录
    logger.debug("\n=== 测试添加 TXT 记录 ===")
    domain = "chrmjj.fun"
    subDomain = "_acme-challenge"
    value = "test_validation_string"

    record_id = provider.add_txt_record(domain, subDomain, value)
    if record_id:
        logger.debug(f"✅ 添加成功，ID: {record_id}")

        # 等待一段时间
        time.sleep(5)

        # 测试获取记录
        logger.debug("\n=== 测试获取记录 ===")
        result = provider.get_record_info(domain, record_id)
        logger.debug(f"记录: {result}")

        # 测试删除记录
        logger.debug("\n=== 测试删除记录 ===")
        success = provider.del_txt_record(domain, record_id)
        logger.debug(f"删除结果: {success}")
    else:
        logger.debug("❌ 添加失败")
