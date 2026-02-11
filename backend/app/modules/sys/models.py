from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, func
from app.core.db.database import metadata, engine
system_config_table = Table(
    "system_config",
    metadata,
    Column("id", Integer, primary_key=True, default=1),
    Column("is_initialized", Boolean, default=False),
    Column("admin_password_hash", String(128)),  # bcrypt 哈希
    Column("created_at", DateTime, server_default=func.now())
)
