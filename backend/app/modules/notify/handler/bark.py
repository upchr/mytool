# notify/bark.py
import httpx
from typing import Dict, Any
from .base import NotificationStrategy

class BarkStrategy(NotificationStrategy):
    """Bark 通知策略"""

    strategy_name = "bark"

    def _validate_config(self):
        """验证Bark配置"""
        required_fields = ['server_url', 'device_key']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Bark配置缺少必要字段: {field}")

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送Bark通知
        """
        base_url = self.config['server_url'].rstrip('/')
        device_key = self.config['device_key']

        url = f"{base_url}/{device_key}"

        # 构建请求参数
        params = {
            'title': title,
            'body': content,
            'level': kwargs.get('level', 'active'),
            'badge': kwargs.get('badge'),
            'autoCopy': kwargs.get('auto_copy', '1'),
            'copy': kwargs.get('copy'),
            'sound': kwargs.get('sound', 'birdsong'),
            'icon': kwargs.get('icon'),
            'group': kwargs.get('group', 'default'),
            'url': kwargs.get('url'),
        }

        # 移除None值
        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                result = response.json()
                return {
                    'success': result.get('code') == 200,
                    'message': result.get('message', ''),
                    'raw_response': result
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': None
            }
