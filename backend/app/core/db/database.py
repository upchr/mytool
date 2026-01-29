import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

"""数据库链接配置"""
if sys.platform.startswith("win"):
    data_dir = Path.cwd().parent.parent / "data"
else:
    # Linux / Docker 挂载卷
    data_dir=Path("/toolsplus/data")

logger.info(f"数据库路径：{data_dir}")
data_dir.mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{data_dir}/notes.db")

# Engine 全局单例
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 特有
)

# Optional: Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 全局 MetaData（供 Core table 定义用）
metadata = MetaData()
