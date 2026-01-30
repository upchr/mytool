# notify/qq.py
import httpx
from typing import Dict, Any
from .base import NotificationStrategy

class QQStrategy(NotificationStrategy):
    """QQ通知策略"""

    strategy_name = "qq"

    def _validate_config(self):
        """验证QQ配置"""
        required_fields = ['api_url']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"QQ配置缺少必要字段: {field}")

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送QQ通知
        """
        api_url = self.config['api_url']

        # 接收者类型：private(私聊) 或 group(群聊)
        message_type = kwargs.get('message_type', 'private')
        target_id = kwargs.get('target_id') or self.config.get('default_target_id')

        if not target_id:
            return {
                'success': False,
                'message': '缺少目标ID (target_id)',
                'raw_response': None
            }

        # 构建消息内容
        full_content = f"{title}\n\n{content}" if title else content

        # 根据不同API格式发送
        if 'coolq' in api_url.lower() or 'cqhttp' in api_url.lower():
            # CoolQ HTTP API 格式
            data = {
                'message_type': message_type,
                message_type + '_id': int(target_id),
                'message': full_content,
                'auto_escape': kwargs.get('auto_escape', False)
            }
        else:
            # 通用格式
            data = {
                'type': message_type,
                'target': target_id,
                'message': full_content,
                'title': title
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()

                result = response.json()
                return {
                    'success': result.get('status') == 'ok' or result.get('retcode') == 0,
                    'message': result.get('msg', ''),
                    'raw_response': result
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': None
            }
