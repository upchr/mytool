from app.core.db.utils.repository import BaseRepository
from app.core.db.database import engine
from sqlalchemy import select, insert, delete, update, desc
from .models import *

class DnsAuthRepository(BaseRepository):
    def __init__(self, engine):
        super().__init__(engine, ssl_dns_auth_table)

    def search_by_name(self, keyword: str):
        stmt = select(self.table).where(
            self.table.c.name.like(f'%{keyword}%')
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row) for row in result.mappings()]


dnsauth_repo = DnsAuthRepository(engine)

