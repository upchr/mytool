# notify/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, ClassVar

class NotificationStrategy(ABC):
    """通知策略抽象基类"""

    # 类属性：策略名称，子类必须设置
    strategy_name: ClassVar[str] = ""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self):
        """验证配置"""
        pass

    @abstractmethod
    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送通知

        Args:
            title: 通知标题
            content: 通知内容
            **kwargs: 额外参数

        Returns:
            发送结果字典
        """
        pass

    @classmethod
    def get_strategy_name(cls) -> str:
        """获取策略名称"""
        return cls.strategy_name

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 可以发送一个测试通知或检查配置
            return True
        except Exception:
            return False
