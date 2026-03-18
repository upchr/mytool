# app/modules/asset/services.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.sql import text, case

from app.modules.asset import models, schemas
from app.core.exception.exceptions import NotFoundException, BusinessException


class AssetService:
    """固定资产服务类"""

    def __init__(self, engine):
        self.engine = engine
        self.table = models.asset_table

    def _calculate_usage_info(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算使用信息（使用天数、日均成本、质保信息）

        Args:
            asset: 资产数据字典

        Returns:
            包含计算字段的资产字典
        """
        purchase_date = asset.get('purchase_date')
        price = asset.get('price', 0)
        status = asset.get('status', 'active')
        scrapped_date = asset.get('scrapped_date')
        warranty_months = asset.get('warranty_months')

        # 确定结束日期（如果已报废，使用报废日期；否则使用当前日期）
        if status == 'scrapped' and scrapped_date:
            end_date = scrapped_date
        else:
            end_date = datetime.now()

        # 计算使用天数
        if purchase_date:
            if end_date >= purchase_date:
                usage_days = (end_date - purchase_date).days
            else:
                usage_days = 0
        else:
            usage_days = 0

        # 计算日均成本
        daily_cost = round(price / usage_days, 2) if usage_days > 0 else price

        # 计算质保信息
        remaining_warranty_days = None
        is_warranty_expired = False
        warranty_expire_date = asset.get('warranty_expire_date')

        if warranty_months and warranty_months > 0:
            if not warranty_expire_date:
                # 如果没有质保到期日期，则计算
                warranty_expire_date = purchase_date + timedelta(days=warranty_months * 30)

            remaining_days = (warranty_expire_date - datetime.now()).days
            remaining_warranty_days = max(0, remaining_days)
            is_warranty_expired = remaining_days < 0

        # 添加计算字段
        asset['usage_days'] = usage_days
        asset['daily_cost'] = daily_cost
        asset['remaining_warranty_days'] = remaining_warranty_days
        asset['is_warranty_expired'] = is_warranty_expired

        return asset

    def create(self, data: schemas.AssetCreate) -> Dict[str, Any]:
        """
        创建固定资产

        Args:
            data: 创建数据

        Returns:
            创建的资产数据
        """
        # 计算质保到期日期
        warranty_expire_date = None
        if data.warranty_months and data.warranty_months > 0:
            warranty_expire_date = data.purchase_date + timedelta(days=data.warranty_months * 30)

        # 构建插入数据
        insert_data = {
            'name': data.name,
            'category': data.category,
            'price': data.price,
            'purchase_date': data.purchase_date,
            'description': data.description,
            'image_url': data.image_url,
            'warranty_months': data.warranty_months,
            'warranty_expire_date': warranty_expire_date,
            'status': 'active',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        with self.engine.connect() as conn:
            result = conn.execute(self.table.insert().values(insert_data))
            conn.commit()
            asset_id = result.inserted_primary_key[0]

        # 获取并返回创建的资产
        return self.get_by_id(asset_id)

    def update(self, asset_id: int, data: schemas.AssetUpdate) -> Optional[Dict[str, Any]]:
        """
        更新固定资产

        Args:
            asset_id: 资产ID
            data: 更新数据

        Returns:
            更新后的资产数据，如果不存在返回 None
        """
        # 获取现有资产
        existing = self.get_by_id(asset_id)
        if not existing:
            return None

        # 构建更新数据（只更新提供的字段）
        update_data = {}
        if data.name is not None:
            update_data['name'] = data.name
        if data.category is not None:
            update_data['category'] = data.category
        if data.price is not None:
            update_data['price'] = data.price
        if data.purchase_date is not None:
            update_data['purchase_date'] = data.purchase_date
        if data.description is not None:
            update_data['description'] = data.description
        if data.image_url is not None:
            update_data['image_url'] = data.image_url
        if data.status is not None:
            update_data['status'] = data.status
        if data.warranty_months is not None:
            update_data['warranty_months'] = data.warranty_months
            # 如果质保期发生变化，重新计算到期日期
            purchase_date = data.purchase_date if data.purchase_date else existing['purchase_date']
            if data.warranty_months > 0:
                update_data['warranty_expire_date'] = purchase_date + timedelta(days=data.warranty_months * 30)
            else:
                update_data['warranty_expire_date'] = None

        update_data['updated_at'] = datetime.now()

        # 执行更新
        with self.engine.connect() as conn:
            conn.execute(
                self.table.update()
                .where(self.table.c.id == asset_id)
                .values(update_data)
            )
            conn.commit()

        return self.get_by_id(asset_id)

    def delete(self, asset_id: int) -> bool:
        """
        删除固定资产

        Args:
            asset_id: 资产ID

        Returns:
            是否删除成功
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                self.table.delete()
                .where(self.table.c.id == asset_id)
            )
            conn.commit()

        return result.rowcount > 0

    def get_by_id(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取固定资产

        Args:
            asset_id: 资产ID

        Returns:
            资产数据，如果不存在返回 None
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(self.table)
                .where(self.table.c.id == asset_id)
            )
            row = result.fetchone()

        if not row:
            return None

        # 转换为字典
        asset = dict(row._mapping)

        # 计算使用信息
        return self._calculate_usage_info(asset)

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> schemas.AssetListResponse:
        """
        获取固定资产列表

        Args:
            page: 页码
            page_size: 每页数量
            category: 资产类别筛选
            status: 状态筛选
            search: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            分页列表响应
        """
        # 构建查询
        query = select(self.table)

        # 筛选条件
        conditions = []
        if category:
            conditions.append(self.table.c.category == category)
        if status:
            conditions.append(self.table.c.status == status)
        if search:
            conditions.append(
                or_(
                    self.table.c.name.like(f'%{search}%'),
                    self.table.c.description.like(f'%{search}%')
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # 排序
        if sort_by:
            sort_column = getattr(self.table.c, sort_by, None)
            if sort_column:
                if sort_order == 'desc':
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            # 默认按购买日期降序排序
            query = query.order_by(desc(self.table.c.purchase_date))

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        with self.engine.connect() as conn:
            result = conn.execute(query)
            items = [dict(row._mapping) for row in result.fetchall()]

        # 计算使用信息
        items = [self._calculate_usage_info(item) for item in items]

        # 获取总数
        count_query = select(func.count()).select_from(self.table)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        with self.engine.connect() as conn:
            total_result = conn.execute(count_query)
            total = total_result.scalar()

        # 计算总页数
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return schemas.AssetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            items=items
        )

    def scrap(self, asset_id: int, scrap_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        报废固定资产

        Args:
            asset_id: 资产ID
            scrap_date: 报废日期，默认为当前时间

        Returns:
            更新后的资产数据，如果不存在返回 None
        """
        if scrap_date is None:
            scrap_date = datetime.now()

        # 更新资产状态
        update_data = {
            'status': 'scrapped',
            'scrapped_date': scrap_date,
            'updated_at': datetime.now()
        }

        with self.engine.connect() as conn:
            result = conn.execute(
                self.table.update()
                .where(self.table.c.id == asset_id)
                .values(update_data)
            )
            conn.commit()

        if result.rowcount == 0:
            return None

        return self.get_by_id(asset_id)

    def batch_delete(self, asset_ids: List[int]) -> int:
        """
        批量删除固定资产

        Args:
            asset_ids: 资产ID列表

        Returns:
            删除的数量
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                self.table.delete()
                .where(self.table.c.id.in_(asset_ids))
            )
            conn.commit()

        return result.rowcount

    def batch_scrap(self, asset_ids: List[int], scrap_date: Optional[datetime] = None) -> int:
        """
        批量报废固定资产

        Args:
            asset_ids: 资产ID列表
            scrap_date: 报废日期，默认为当前时间

        Returns:
            报废的数量
        """
        if scrap_date is None:
            scrap_date = datetime.now()

        update_data = {
            'status': 'scrapped',
            'scrapped_date': scrap_date,
            'updated_at': datetime.now()
        }

        with self.engine.connect() as conn:
            result = conn.execute(
                self.table.update()
                .where(self.table.c.id.in_(asset_ids))
                .values(update_data)
            )
            conn.commit()

        return result.rowcount

    def get_stats(self) -> schemas.AssetStats:
        """
        获取固定资产统计信息

        Returns:
            统计信息
        """
        with self.engine.connect() as conn:
            # 总数和状态统计
            total_result = conn.execute(
                select(
                    func.count().label('total'),
                    func.sum(
                        case((self.table.c.status == 'active', 1), else_=0)
                    ).label('active'),
                    func.sum(
                        case((self.table.c.status == 'scrapped', 1), else_=0)
                    ).label('scrapped'),
                    func.sum(self.table.c.price).label('total_value')
                )
                .select_from(self.table)
            )
            stats_row = total_result.fetchone()

            total = stats_row.total or 0
            active = stats_row.active or 0
            scrapped = stats_row.scrapped or 0
            total_value = float(stats_row.total_value or 0)

            # 计算日均成本总和
            daily_cost_sum = 0.0
            if total > 0:
                # 获取所有资产并计算日均成本
                all_assets = conn.execute(select(self.table)).fetchall()
                for asset in all_assets:
                    asset_dict = dict(asset._mapping)
                    calculated = self._calculate_usage_info(asset_dict)
                    daily_cost_sum += calculated['daily_cost']
                daily_cost_sum = round(daily_cost_sum, 2)

            # 按类别统计
            category_result = conn.execute(
                select(
                    self.table.c.category,
                    func.count().label('count'),
                    func.sum(self.table.c.price).label('value')
                )
                .group_by(self.table.c.category)
            )
            by_category = {}
            for row in category_result.fetchall():
                by_category[row.category] = {
                    'count': row.count,
                    'value': float(row.value or 0)
                }

            # 按年份统计
            year_result = conn.execute(
                select(
                    func.strftime('%Y', self.table.c.purchase_date).label('year'),
                    func.count().label('count'),
                    func.sum(self.table.c.price).label('value')
                )
                .group_by(func.strftime('%Y', self.table.c.purchase_date))
                .order_by(func.strftime('%Y', self.table.c.purchase_date).desc())
            )
            by_year = {}
            for row in year_result.fetchall():
                year = int(row.year) if row.year else 0
                by_year[year] = {
                    'count': row.count,
                    'value': float(row.value or 0)
                }

        return schemas.AssetStats(
            total=total,
            active=active,
            scrapped=scrapped,
            total_value=total_value,
            daily_cost_sum=daily_cost_sum,
            by_category=by_category,
            by_year=by_year
        )

    def get_category_distribution(self) -> List[schemas.CategoryDistribution]:
        """
        获取资产类别分布

        Returns:
            类别分布列表
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(
                    self.table.c.category,
                    func.count().label('count'),
                    func.sum(self.table.c.price).label('value')
                )
                .group_by(self.table.c.category)
                .order_by(desc(func.sum(self.table.c.price)))
            )

            total = conn.execute(select(func.count()).select_from(self.table)).scalar()

        distribution = []
        for row in result.fetchall():
            distribution.append(
                schemas.CategoryDistribution(
                    category=row.category,
                    count=row.count,
                    value=float(row.value or 0),
                    percentage=round((row.count / total * 100), 2) if total > 0 else 0
                )
            )

        return distribution

    def get_year_trend(self, limit: int = 10) -> List[schemas.YearTrend]:
        """
        获取年度购买趋势

        Args:
            limit: 返回的年份数量限制

        Returns:
            年度趋势列表
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(
                    func.strftime('%Y', self.table.c.purchase_date).label('year'),
                    func.count().label('count'),
                    func.sum(self.table.c.price).label('value')
                )
                .group_by(func.strftime('%Y', self.table.c.purchase_date))
                .order_by(func.strftime('%Y', self.table.c.purchase_date).desc())
                .limit(limit)
            )

        trends = []
        for row in result.fetchall():
            trends.append(
                schemas.YearTrend(
                    year=int(row.year) if row.year else 0,
                    count=row.count,
                    value=float(row.value or 0)
                )
            )

        return trends

    def get_top_value_assets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取价值最高的资产

        Args:
            limit: 返回数量限制

        Returns:
            资产列表
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(self.table)
                .where(self.table.c.status == 'active')
                .order_by(desc(self.table.c.price))
                .limit(limit)
            )

        assets = [self._calculate_usage_info(dict(row._mapping)) for row in result.fetchall()]
        return assets

    def get_expiring_warranty_assets(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取即将过质保的资产

        Args:
            days: 天数阈值

        Returns:
            资产列表
        """
        future_date = datetime.now() + timedelta(days=days)

        with self.engine.connect() as conn:
            result = conn.execute(
                select(self.table)
                .where(
                    and_(
                        self.table.c.status == 'active',
                        self.table.c.warranty_expire_date.isnot(None),
                        self.table.c.warranty_expire_date <= future_date
                    )
                )
                .order_by(asc(self.table.c.warranty_expire_date))
            )

        assets = [self._calculate_usage_info(dict(row._mapping)) for row in result.fetchall()]
        return assets


__all__ = ["AssetService"]
