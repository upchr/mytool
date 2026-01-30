# notify/mail.py
import smtplib
import ssl
# 使用绝对导入避免冲突
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from .base import NotificationStrategy

class EmailStrategy(NotificationStrategy):
    """邮件通知策略"""

    strategy_name = "email"

    def _validate_config(self):
        """验证邮件配置"""
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'from_email']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"邮件配置缺少必要字段: {field}")

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送邮件通知
        """
        # 获取收件人
        to_emails = kwargs.get('to_emails') or self.config.get('default_to_emails')
        if not to_emails:
            return {
                'success': False,
                'message': '缺少收件人地址',
                'raw_response': None
            }

        if isinstance(to_emails, str):
            to_emails = [to_emails]

        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = self.config['from_email']
        message["To"] = ", ".join(to_emails)

        # 添加纯文本和HTML版本
        text_part = MIMEText(content, "plain", "utf-8")
        html_content = content.replace('\n', '<br>')
        html_part = MIMEText(f"""
        <html>
            <body>
                <h2>{title}</h2>
                <p>{html_content}</p>
            </body>
        </html>
        """, "html", "utf-8")

        message.attach(text_part)
        message.attach(html_part)

        try:
            # 使用SSL连接
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(
                    self.config['smtp_server'],
                    self.config['smtp_port'],
                    context=context
            ) as server:
                server.login(self.config['username'], self.config['password'])
                server.send_message(message)

            return {
                'success': True,
                'message': '邮件发送成功',
                'raw_response': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': None
            }
