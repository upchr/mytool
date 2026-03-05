# app/core/utils/path_utils.py
import logging
import sys
from pathlib import Path
from functools import lru_cache
logger = logging.getLogger(__name__)

class PathUtils:
    """路径工具类"""

    is_win = sys.platform.startswith("win")

    def print_paths(self):
        """打印所有路径（只执行一次）"""
        logger.info("=" * 50)
        logger.info("📁 路径初始化信息")
        logger.info(f"project_root: {self.get_project_root()}")
        logger.info(f"app_dir: {self.get_app_dir()}")
        logger.info(f"app_modules_dir: {self.get_app_modules_dir()}")

        logger.info(f"data_dir: {self.get_data_dir()}")
        logger.info(f"cert_dir: {self.get_cert_dir()}")
        logger.info(f"log_dir: {self.get_log_dir()}")
        logger.info(f"version_dir: {self.get_version_dir()}")
        logger.info("=" * 50)

    @classmethod
    @lru_cache(maxsize=1)
    def get_app_dir(cls) -> Path:
        """获取 app 目录（带缓存）"""
        current_file = Path(__file__).resolve()

        for parent in current_file.parents:
            if parent.name == 'app':
                return parent

        app_dir = current_file.parent.parent.parent
        if app_dir.name == 'app':
            return app_dir

        raise RuntimeError(f"无法定位 app 目录，当前文件: {current_file}")

    @classmethod
    @lru_cache(maxsize=1)
    def get_app_modules_dir(cls) -> Path:
        return cls.get_app_dir() / "modules"

    @classmethod
    @lru_cache(maxsize=1)
    def get_project_root(cls) -> Path:
        """获取项目根目录"""
        return cls.get_app_dir().parent

    @classmethod
    @lru_cache(maxsize=1)
    def get_data_dir(cls) -> Path:
        """获取数据目录"""
        if cls.is_win:
            return cls.get_project_root().parent / "data"
        else:
            return Path("/toolsplus/data")

    @classmethod
    def get_cert_dir(cls, subdir: str = None) -> Path:
        """获取证书目录（注意：subdir 参数会导致缓存失效）"""
        cert_dir = cls.get_data_dir() / 'certs'
        if subdir:
            cert_dir = cert_dir / subdir
        cert_dir.mkdir(exist_ok=True, parents=True)
        return cert_dir

    @classmethod
    @lru_cache(maxsize=1)
    def get_log_dir(cls) -> Path:
        """获取日志目录"""
        log_dir = cls.get_data_dir() / 'logs'
        log_dir.mkdir(exist_ok=True, parents=True)
        return log_dir

    @classmethod
    @lru_cache(maxsize=1)
    def get_version_dir(cls) -> Path:
        return cls.get_project_root() if cls.is_win else Path("/toolsplus")
# 导出实例
path_utils = PathUtils()

