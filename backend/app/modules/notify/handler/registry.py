# notify/registry.py
"""
通知策略注册表
在此文件中导入所有策略模块，确保它们被正确注册
"""

# 导入所有策略模块（按需）
from .bark import BarkStrategy
from .wxcom import WechatStrategy
from .qq import QQStrategy
from .mail import EmailStrategy
from .dingtalk import DingtalkStrategy

# 可选：在导入时打印信息
print(f"通知策略注册表已导入，共 {len([x for x in locals().values() if hasattr(x, 'strategy_name')])} 个策略类")
