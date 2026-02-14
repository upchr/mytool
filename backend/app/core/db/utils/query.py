#app/core/db/utils/query.py
from sqlalchemy import select, func, and_, or_

class QueryBuilder:
    """查询构建器，让 Core 用起来像 ORM 一样方便"""

    def __init__(self, table):
        self.table = table
        self._query = select(table)
        self._conditions = []

    def where(self, condition):
        self._conditions.append(condition)
        return self

    def where_eq(self, field, value):
        return self.where(self.table.c[field] == value)

    def where_like(self, field, pattern):
        return self.where(self.table.c[field].like(pattern))

    def where_in(self, field, values):
        return self.where(self.table.c[field].in_(values))

    def order_by(self, *fields):
        self._query = self._query.order_by(*fields)
        return self

    def limit(self, n):
        self._query = self._query.limit(n)
        return self

    def offset(self, n):
        self._query = self._query.offset(n)
        return self

    def build(self):
        if self._conditions:
            self._query = self._query.where(and_(*self._conditions))
        return self._query

    def execute(self, engine):
        with engine.connect() as conn:
            result = conn.execute(self.build())
            return [dict(row) for row in result.mappings()]

# 使用示例
# from app.core.db.query import QueryBuilder
#
# notes = (QueryBuilder(notes_table)
#          .where_eq('is_active', True)
#          .where_like('title', '%test%')
#          .order_by(desc(notes_table.c.created_at))
#          .limit(10)
#          .execute(engine))
