#app/core/db/utils/query.py
from sqlalchemy import select, func, and_, or_, text
from typing import Dict, Any


class QueryBuilder:
    """查询构建器，让 Core 用起来像 ORM 一样方便"""

    def __init__(self, table):
        self.table = table
        self._query = select(table)
        self._conditions = []

    def where(self, condition):
        """支持列对象和文本条件"""
        if isinstance(condition, str):
            # 如果是字符串，自动包装为 text
            condition = text(condition)
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

    def paginate(self, engine, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        分页查询

        Args:
            engine: 数据库引擎
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            分页结果字典，包含：
                - items: 数据列表
                - total: 总记录数
                - page: 当前页码
                - page_size: 每页数量
                - pages: 总页数
        """
        # 构建查询
        query = self.build()

        # 获取总数
        count_query = select(func.count()).select_from(query.alias())
        with engine.connect() as conn:
            total = conn.execute(count_query).scalar()

        # 添加分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询获取数据
        with engine.connect() as conn:
            result = conn.execute(query)
            items = [dict(row) for row in result.mappings()]

        # 计算总页数
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': pages
        }

# 使用示例
# from app.core.db.query import QueryBuilder
#
# notes = (QueryBuilder(notes_table)
#          .where_eq('is_active', True)
#          .where_like('title', '%test%')
#          .order_by(desc(notes_table.c.created_at))
#          .limit(10)
#          .execute(engine))
