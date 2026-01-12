import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

if sys.platform.startswith("win"):
    # Windows 下使用绝对路径
    BASE_DIR = os.path.abspath("./data")
    os.makedirs(BASE_DIR, exist_ok=True)
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/notes.db")
else:
    # Linux / Docker 挂载卷
    os.makedirs("/data", exist_ok=True)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/notes.db")

# Engine 全局单例
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 特有
)

# Optional: Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 全局 MetaData（供 Core table 定义用）
metadata = MetaData()
