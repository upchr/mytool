#app/core/db/database.py
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

"""数据库链接配置"""
from app.core.utils.path_utils import path_utils
data_dir=path_utils.get_data_dir()
# if sys.platform.startswith("win"):
#     data_dir = Path.cwd().parent.parent / "data"
# else:
#     # Linux / Docker 挂载卷
#     data_dir=Path("/toolsplus/data")

logger.info(f"数据库路径：{data_dir}")
data_dir.mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{data_dir}/notes.db")

# Engine 全局单例
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 特有
)

def get_engine():
    return engine

# Optional: Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 全局 MetaData（供 Core table 定义用）
metadata = MetaData()

# ========== 添加 database 对象以兼容异步访问 ==========

class Database:
    """数据库访问适配器，提供异步风格的接口供 plugin/stats 等模块使用"""

    @staticmethod
    async def fetch_one(query: Any) -> Optional[Dict]:
        """获取单条记录"""
        import asyncio
        loop = asyncio.get_running_loop()
        def _fetch():
            with engine.connect() as conn:
                result = conn.execute(query).fetchone()
                return dict(result._mapping) if result else None
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    async def fetch_all(query: Any) -> List[Dict]:
        """获取所有记录"""
        import asyncio
        loop = asyncio.get_running_loop()
        def _fetch():
            with engine.connect() as conn:
                return [dict(row._mapping) for row in conn.execute(query).fetchall()]
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    async def fetch_val(query: Any, column: Any = None) -> Any:
        """获取单个值"""
        import asyncio
        loop = asyncio.get_running_loop()
        def _fetch():
            with engine.connect() as conn:
                result = conn.execute(query).scalar()
                return result
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    async def execute(query: Any) -> Any:
        """执行查询（insert/update/delete）"""
        import asyncio
        loop = asyncio.get_running_loop()
        def _exec():
            with engine.begin() as conn:
                result = conn.execute(query)
                return result.inserted_primary_key[0] if result.inserted_primary_key else result.rowcount
        return await loop.run_in_executor(None, _exec)

# 创建 database 对象
database = Database()
