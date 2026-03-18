# app/modules/task_template/services.py
"""
任务模板模块 - 业务逻辑层

包含：
- TaskTemplateService: 模板管理服务
- 内置模板定义（天气推送等）
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func

from app.core.db.utils.query import QueryBuilder
from app.modules.task_template.models import task_templates_table
from app.modules.task_template import schemas

logger = logging.getLogger(__name__)


# ========== 内置模板定义 ==========

BUILTIN_TEMPLATES = [
    # ========== 天气推送模板 ==========
    {
        "template_id": "weather-push",
        "name": "天气推送",
        "description": "定时获取天气信息并推送到指定渠道",
        "category": "通知推送",
        "tags": ["天气", "推送", "通知"],
        "icon": "🌤️",
        "script_type": "shell",
        "script_content": '''#!/bin/bash
# 天气推送脚本
# 使用 wttr.in 获取天气信息

CITY="${CITY:-北京}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
PUSH_TYPE="${PUSH_TYPE:-feishu}"

# 获取天气信息
WEATHER_DATA=$(curl -s "https://wttr.in/${CITY}?format=%t+%C+%h+%w")

# 构建推送消息
MESSAGE="🌤️ ${CITY} 天气预报\\n温度: $(echo $WEATHER_DATA | cut -d' ' -f1)\\n天气: $(echo $WEATHER_DATA | cut -d' ' -f2)\\n湿度: $(echo $WEATHER_DATA | cut -d' ' -f3)\\n风速: $(echo $WEATHER_DATA | cut -d' ' -f4)"

if [ -n "$WEBHOOK_URL" ]; then
    # 飞书推送
    if [ "$PUSH_TYPE" = "feishu" ]; then
        curl -s -X POST "$WEBHOOK_URL" \\
            -H "Content-Type: application/json" \\
            -d "{
                \\"msg_type\\": \\"text\\",
                \\"content\\": {\\"text\\": \\"$MESSAGE\\"}
            }"
    # 企业微信推送
    elif [ "$PUSH_TYPE" = "wecom" ]; then
        curl -s -X POST "$WEBHOOK_URL" \\
            -H "Content-Type: application/json" \\
            -d "{
                \\"msgtype\\": \\"text\\",
                \\"text\\": {\\"content\\": \\"$MESSAGE\\"}
            }"
    # 钉钉推送
    elif [ "$PUSH_TYPE" = "dingtalk" ]; then
        curl -s -X POST "$WEBHOOK_URL" \\
            -H "Content-Type: application/json" \\
            -d "{
                \\"msgtype\\": \\"text\\",
                \\"text\\": {\\"content\\": \\"$MESSAGE\\"}
            }"
    fi
    echo "天气推送成功: $WEATHER_DATA"
else
    echo "天气信息: $WEATHER_DATA"
fi
''',
        "config_schema": {
            "type": "object",
            "properties": {
                "CITY": {
                    "type": "string",
                    "title": "城市",
                    "default": "北京",
                    "description": "查询天气的城市名称"
                },
                "WEBHOOK_URL": {
                    "type": "string",
                    "title": "Webhook 地址",
                    "description": "推送的 Webhook 地址"
                },
                "PUSH_TYPE": {
                    "type": "string",
                    "title": "推送类型",
                    "enum": ["feishu", "wecom", "dingtalk"],
                    "default": "feishu",
                    "description": "推送渠道类型"
                }
            }
        },
        "default_cron": "0 8 * * *",
        "cron_description": "每天早上8点推送天气",
        "is_official": True,
        "is_active": True
    },
    
    # ========== 系统监控模板 ==========
    {
        "template_id": "system-monitor",
        "name": "系统监控",
        "description": "监控系统CPU、内存、磁盘使用率并告警",
        "category": "系统运维",
        "tags": ["监控", "告警", "运维"],
        "icon": "📊",
        "script_type": "shell",
        "script_content": '''#!/bin/bash
# 系统监控脚本

CPU_THRESHOLD="${CPU_THRESHOLD:-80}"
MEM_THRESHOLD="${MEM_THRESHOLD:-80}"
DISK_THRESHOLD="${DISK_THRESHOLD:-80}"
WEBHOOK_URL="${WEBHOOK_URL:-}"

# 获取CPU使用率
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')

# 获取内存使用率
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

# 获取磁盘使用率
DISK_USAGE=$(df -h / | tail -1 | awk '{print int($5)}')

ALERT_MSG=""

if [ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ]; then
    ALERT_MSG="${ALERT_MSG}⚠️ CPU使用率: ${CPU_USAGE}%\\n"
fi

if [ "$MEM_USAGE" -gt "$MEM_THRESHOLD" ]; then
    ALERT_MSG="${ALERT_MSG}⚠️ 内存使用率: ${MEM_USAGE}%\\n"
fi

if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
    ALERT_MSG="${ALERT_MSG}⚠️ 磁盘使用率: ${DISK_USAGE}%\\n"
fi

if [ -n "$ALERT_MSG" ] && [ -n "$WEBHOOK_URL" ]; then
    curl -s -X POST "$WEBHOOK_URL" \\
        -H "Content-Type: application/json" \\
        -d "{\\"msg_type\\": \\"text\\", \\"content\\": {\\"text\\": \\"系统监控告警\\n$ALERT_MSG\\"}}"
    echo "告警已发送"
else
    echo "系统状态正常 - CPU: ${CPU_USAGE}% 内存: ${MEM_USAGE}% 磁盘: ${DISK_USAGE}%"
fi
''',
        "config_schema": {
            "type": "object",
            "properties": {
                "CPU_THRESHOLD": {
                    "type": "integer",
                    "title": "CPU阈值",
                    "default": 80,
                    "description": "CPU使用率告警阈值(%)"
                },
                "MEM_THRESHOLD": {
                    "type": "integer",
                    "title": "内存阈值",
                    "default": 80,
                    "description": "内存使用率告警阈值(%)"
                },
                "DISK_THRESHOLD": {
                    "type": "integer",
                    "title": "磁盘阈值",
                    "default": 80,
                    "description": "磁盘使用率告警阈值(%)"
                },
                "WEBHOOK_URL": {
                    "type": "string",
                    "title": "告警Webhook",
                    "description": "告警推送地址"
                }
            }
        },
        "default_cron": "*/5 * * * *",
        "cron_description": "每5分钟检查一次",
        "is_official": True,
        "is_active": True
    },
    
    # ========== 数据库备份模板 ==========
    {
        "template_id": "db-backup",
        "name": "数据库备份",
        "description": "定时备份数据库文件",
        "category": "数据备份",
        "tags": ["备份", "数据库", "运维"],
        "icon": "💾",
        "script_type": "shell",
        "script_content": '''#!/bin/bash
# 数据库备份脚本

BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
DB_PATH="${DB_PATH:-/data/app.db}"
RETAIN_DAYS="${RETAIN_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_${DATE}.db"

cp "$DB_PATH" "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"

# 清理旧备份
find "$BACKUP_DIR" -name "*.db.gz" -mtime +${RETAIN_DAYS} -delete

echo "数据库备份完成: ${BACKUP_FILE}.gz"
''',
        "config_schema": {
            "type": "object",
            "properties": {
                "BACKUP_DIR": {
                    "type": "string",
                    "title": "备份目录",
                    "default": "/data/backups",
                    "description": "备份文件存储目录"
                },
                "DB_PATH": {
                    "type": "string",
                    "title": "数据库路径",
                    "default": "/data/app.db",
                    "description": "数据库文件路径"
                },
                "RETAIN_DAYS": {
                    "type": "integer",
                    "title": "保留天数",
                    "default": 7,
                    "description": "备份保留天数"
                }
            }
        },
        "default_cron": "0 2 * * *",
        "cron_description": "每天凌晨2点备份",
        "is_official": True,
        "is_active": True
    },
]


class TaskTemplateRepository:
    """任务模板数据访问层"""
    
    def __init__(self, engine):
        self.engine = engine
        self.table = task_templates_table
    
    def create(self, data: Dict[str, Any]) -> int:
        """创建模板"""
        query = self.table.insert().values(**data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]
    
    def update(self, template_id: str, data: Dict[str, Any]) -> bool:
        """更新模板"""
        query = (
            self.table.update()
            .where(self.table.c.template_id == template_id)
            .values(**data)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0
    
    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """根据 template_id 获取模板"""
        query = select(self.table).where(self.table.c.template_id == template_id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取模板列表（分页）"""
        query = QueryBuilder(self.table)
        query.where_eq('is_active', True)
        
        for key, value in filters.items():
            if value is not None:
                if key == 'keyword':
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.table.c, key):
                    query.where_eq(key, value)
        
        return query.paginate(self.engine, page, page_size)
    
    def increment_download(self, template_id: str) -> bool:
        """增加下载次数"""
        query = (
            self.table.update()
            .where(self.table.c.template_id == template_id)
            .values(download_count=self.table.c.download_count + 1)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0


class TaskTemplateService:
    """任务模板管理服务"""
    
    def __init__(self, engine):
        self.repo = TaskTemplateRepository(engine)
        self.engine = engine
    
    def create(self, data: schemas.TaskTemplateCreate) -> Dict[str, Any]:
        """创建模板"""
        create_data = data.model_dump()
        now = datetime.now()
        create_data.update({
            "created_at": now,
            "updated_at": now
        })
        
        template_id = self.repo.create(create_data)
        return self.repo.get_by_id(data.template_id)
    
    def update(self, template_id: str, data: schemas.TaskTemplateUpdate) -> Optional[Dict[str, Any]]:
        """更新模板"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.repo.get_by_id(template_id)
        
        update_data["updated_at"] = datetime.now()
        self.repo.update(template_id, update_data)
        return self.repo.get_by_id(template_id)
    
    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板详情"""
        return self.repo.get_by_id(template_id)
    
    def get_list(self, params: schemas.TaskTemplateQueryParams) -> Dict[str, Any]:
        """获取模板列表"""
        return self.repo.get_list(
            page=params.page,
            page_size=params.page_size,
            category=params.category,
            is_official=params.is_official,
            keyword=params.keyword
        )
    
    def apply_template(self, data: schemas.TemplateApplyRequest) -> Dict[str, Any]:
        """
        应用模板 - 创建 cron 任务
        
        Args:
            data: 应用请求数据
        
        Returns:
            创建的任务信息
        """
        from app.modules.cron.services import create_cron_job
        from app.modules.cron.schemas import CronJobCreate
        
        # 获取模板
        template = self.repo.get_by_id(data.template_id)
        if not template:
            raise ValueError(f"模板不存在: {data.template_id}")
        
        # 增加下载次数
        self.repo.increment_download(data.template_id)
        
        # 变量替换
        script_content = template["script_content"] or ""
        for var_name, var_value in data.variables.items():
            script_content = script_content.replace(f"${{{var_name}}}", str(var_value))
            script_content = script_content.replace(f"${var_name}", str(var_value))
        
        # 创建 cron 任务
        cron_data = CronJobCreate(
            name=data.name or f"{template['name']} - 从模板创建",
            description=data.description or template["description"],
            node_id=data.node_id,
            command=script_content,
            schedule=data.schedule or template["default_cron"] or "0 0 * * *",
            is_active=data.is_active if data.is_active is not None else False
        )
        
        # 调用 cron 模块创建任务
        result = create_cron_job(self.engine, cron_data)
        
        return {
            "message": "模板应用成功",
            "template_id": data.template_id,
            "cron_job": result
        }
    
    def init_builtin_templates(self):
        """初始化内置模板"""
        for template_data in BUILTIN_TEMPLATES:
            existing = self.repo.get_by_id(template_data["template_id"])
            if existing:
                continue
            
            now = datetime.now()
            template_data.update({
                "created_at": now,
                "updated_at": now
            })
            self.repo.create(template_data)
            logger.info(f"内置模板初始化: {template_data['template_id']}")


__all__ = ["TaskTemplateService", "BUILTIN_TEMPLATES"]
