# strategies/dingtalk.py
import httpx
import json
import hashlib
import base64
import hmac
import time
from urllib.parse import quote_plus
from typing import Dict, Any
from .base import NotificationStrategy

class DingtalkStrategy(NotificationStrategy):
    """钉钉机器人通知策略"""
    strategy_name = "dingtalk"

    def _validate_config(self):
        """验证钉钉配置"""
        required_fields = ['webhook_url', 'access_token']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"钉钉配置缺少必要字段: {field}")

    def _sign_url(self, secret: str) -> str:
        """生成带签名的URL"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{secret}'
        sign = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return f"&timestamp={timestamp}&sign={quote_plus(sign)}"

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送钉钉机器人通知
        """
        access_token = self.config['access_token']
        secret = self.config.get('secret', '')

        # 构建URL
        base_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
        if secret:
            base_url += self._sign_url(secret)

        # 构建消息
        data = {
            "msgtype": "text",
            "text": {
                "content": f"{title}\n\n{content}"
            },
            "at": {
                "atMobiles": kwargs.get('at_mobiles', []),
                "isAtAll": kwargs.get('is_at_all', False)
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    base_url,
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()

                result = response.json()
                return {
                    'success': result.get('errcode') == 0,
                    'message': result.get('errmsg', ''),
                    'raw_response': result
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': None
            }
