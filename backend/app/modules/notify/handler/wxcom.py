import httpx
from typing import Dict, Any
from .base import NotificationStrategy

class WechatStrategy(NotificationStrategy):
    """企业微信机器人通知策略"""

    strategy_name = "wecom"

    def _validate_config(self):
        """验证企业微信配置"""
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"企业微信配置缺少必要字段: {field}")

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送企业微信机器人通知
        """
        webhook_url = self.config['webhook_url']

        # 默认使用markdown格式
        msg_type = kwargs.get('msg_type', 'markdown')

        if msg_type == 'text':
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}",
                    "mentioned_list": kwargs.get('mentioned_list', []),
                    "mentioned_mobile_list": kwargs.get('mentioned_mobile_list', [])
                }
            }
        elif msg_type == 'markdown':
            data = {
                "msgtype": "markdown_v2",
                "markdown_v2": {
                    "content": f"**{title}**\n\n{content}"
                }
            }
        elif msg_type == 'news':
            data = {
                "msgtype": "news",
                "news": {
                    "articles": [
                        {
                            "title": title,
                            "description": content[:100] + "..." if len(content) > 100 else content,
                            "url": kwargs.get('url'),
                            "picurl": kwargs.get('image_url')
                        }
                    ]
                }
            }
        else:
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
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
