# ToolsPlus 项目 - AI 开发规范文档
## 📚 文档导航

| 文档 | 用途                       |
|------|--------------------------|
| [AGENTS.md](AGENTS.md) | 项目概览                     |
| [AI开发规范文档.md](AI开发规范文档.md) ⭐ | ai 自主开发完整规范说明（本文档）         |
| [通用组件使用规范.md](通用组件使用规范.md) | DialogForm 组件和全局方法使用详细说明 |

## 文档概述

基于 ToolsPlus 项目（参考“证书管理”模块的前后端代码：`backend/app/modules/acme`、`frontend/src/modules/ssl`）制定的统一 AI 开发规范。

### 🎯 AI 开发流程

```
1. 了解项目 → AGENTS.md
2. 学习规范 → 本文档
3. 研究示例 → backend/app/modules/acme、frontend/src/modules/ssl
4. 使用模板 → 本文档第五章
5. 检查代码 → 使用检查清单
```

**版本**：v1.1 | **更新**：2026-03-18

---

## 一、后端开发规范

### 1.1 目录结构

```
backend/app/modules/{module_name}/
├── __init__.py       # 模块初始化
├── api.py            # FastAPI 路由（自动注册）
├── models.py         # SQLAlchemy Table 定义
├── schemas.py        # Pydantic v2 模式
├── services.py       # 业务逻辑
└── repository.py     # 数据访问层（可选）
```

### 1.2 路由定义（api.py）

**核心模式：**
```python
from fastapi import APIRouter, Depends, Query
from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.{module_name} import schemas, services

router = APIRouter(prefix="/{module-path}", tags=["{中文标签}"])

@router.post("/resource", response_model=BaseResponse[schemas.ResourceRead])
async def create_resource(
    data: schemas.ResourceCreate,
    engine=Depends(get_engine)
):
    """
    创建资源
    
    Args:
        data: 创建数据
        engine: 数据库引擎（依赖注入）
    
    Returns:
        BaseResponse: 统一响应格式
    """
    try:
        service = services.ResourceService(engine)
        result = service.create(data)
        return BaseResponse.success(result)
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))
```

**规范要点：**
- 路由必须包含 `prefix` 和 `tags`
- 使用 `BaseResponse.success/error` 包装响应
- 使用依赖注入 `get_engine`
- 参数验证使用 `Query`、`Path`、`Body`

### 1.3 数据模型（models.py）

**核心模式：**
```python
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean
from app.core.db.database import metadata

resource_table = Table(
    "resource",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False, description="资源名称"),
    Column("description", String(500), description="描述"),
    Column("is_active", Boolean, default=True, description="是否启用"),
    Column("created_at", DateTime, default=datetime.now, description="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, description="更新时间"),
    sqlite_autoincrement=True,
)

__all__ = ["resource_table"]
```

**规范要点：**
- 使用 `Table` 定义（非 ORM 类）
- 必须包含 `created_at` 和 `updated_at`
- 使用 `description` 添加字段说明

### 1.4 Pydantic 模式（schemas.py）

**核心模式：**
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ResourceBase(BaseModel):
    """资源基础Schema"""
    name: str = Field(..., description="资源名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述", max_length=500)
    is_active: bool = Field(True, description="是否启用")

class ResourceCreate(ResourceBase):
    """创建资源"""
    pass

class ResourceUpdate(BaseModel):
    """更新资源"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class ResourceRead(ResourceBase):
    """资源读取"""
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResourceListResponse(BaseModel):
    """资源列表响应"""
    total: int
    page: int
    page_size: int
    pages: int
    items: List[ResourceRead]
```

**规范要点：**
- 使用 Pydantic v2 语法
- Schema 层次：Base → Create/Update → Read
- 使用 `Field(...)` 必填，`Field(None)` 可选
- `model_config = ConfigDict(from_attributes=True)`

### 1.5 业务逻辑层（services.py）

**核心模式：**
```python
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.db.utils.query import QueryBuilder
from app.modules.{module_name} import schemas
from app.modules.{module_name}.repository import ResourceRepository

logger = logging.getLogger(__name__)

class ResourceService:
    """资源服务类"""

    def __init__(self, engine):
        self.repo = ResourceRepository(engine)

    def create(self, data: schemas.ResourceCreate) -> Dict[str, Any]:
        """创建资源"""
        create_data = data.model_dump()
        create_data.update({"created_at": datetime.now(), "updated_at": datetime.now()})
        id = self.repo.create(create_data)
        return self.get_by_id(id)

    def update(self, id: int, data: schemas.ResourceUpdate) -> Optional[Dict[str, Any]]:
        """更新资源"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_by_id(id)
        update_data["updated_at"] = datetime.now()
        success = self.repo.update(id, update_data)
        return self.get_by_id(id) if success else None

    def delete(self, id: int) -> bool:
        """删除资源"""
        return self.repo.delete(id)

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取资源"""
        return self.repo.get_by_id(id)

    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取资源列表（分页）"""
        query = QueryBuilder(self.repo.table)
        
        for key, value in filters.items():
            if value is not None:
                if key == 'search':
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.repo.table.c, key):
                    query.where_eq(key, value)
        
        return query.paginate(self.repo.engine, page, page_size)
```

**规范要点：**
- 使用 `data.model_dump()` 转换数据
- 使用 `exclude_unset=True` 处理更新
- 使用 `QueryBuilder` 进行查询

### 1.6 数据访问层（repository.py）

**核心模式：**
```python
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from app.modules.{module_name}.models import resource_table

class ResourceRepository:
    """资源数据访问类"""

    def __init__(self, engine):
        self.engine = engine
        self.table = resource_table

    def create(self, data: Dict[str, Any]) -> int:
        """创建记录"""
        query = self.table.insert().values(data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]

    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """更新记录"""
        query = self.table.update().where(self.table.c.id == id).values(data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0

    def delete(self, id: int) -> bool:
        """删除记录"""
        query = self.table.delete().where(self.table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        query = select(self.table).where(self.table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
```

**规范要点：**
- 使用 `with self.engine.connect()` 管理连接
- 使用 `conn.commit()` 提交事务
- 返回 `dict(row._mapping)` 转换结果

### 1.7 统一响应和异常处理

```python
from app.core.pojo.response import BaseResponse
from app.core.exception.exceptions import NotFoundException

# 统一响应
return BaseResponse.success(data=result, message="操作成功")
return BaseResponse.error(code=404, message="资源不存在")

# 异常处理
try:
    result = service.some_operation()
except ValueError as e:
    return BaseResponse.error(400, str(e))
except NotFoundException as e:
    return BaseResponse.error(404, e.detail)
except Exception as e:
    logger.error(f"操作失败: {e}")
    return BaseResponse.error(500, str(e))
```

---

## 二、前端开发规范

### 2.1 目录结构

```
frontend/src/modules/{module_name}/
└── ComponentName.vue
```

### 2.2 组件核心模式

```vue
<template>
  <n-card title="资源管理">
    <!-- 工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-input v-model:value="searchKeyword" placeholder="搜索" @keyup.enter="loadResources" />
      <n-button type="primary" @click="handleAdd">新建</n-button>
    </n-space>

    <!-- 表格 -->
    <n-data-table :columns="columns" :data="data" :loading="loading" :pagination="pagination" remote />

    <!-- 表单对话框 -->
    <DialogForm
        ref="dialogRef"
        v-model:visible="showDialog"
        v-model:formData="formData"
        :field-groups="fieldGroups"
        :rules="formRules"
        :title="dialogTitle"
        @submit="handleSubmit"
    />
  </n-card>
</template>

<script setup>
import {h, ref, reactive, computed, onMounted} from 'vue'
import {NButton, NSpace} from 'naive-ui'
import DialogForm from '@/components/DialogForm.vue'

// 状态
const loading = ref(false)
const data = ref([])
const searchKeyword = ref('')
const showDialog = ref(false)
const dialogType = ref('add')
const dialogRef = ref(null)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  onChange: (page) => { pagination.page = page; loadResources() }
})

// 表单
const formData = ref({})
const defaultFormData = {name: '', description: '', is_active: true}

// 表格列
const columns = [
  {title: 'ID', key: 'id', width: 80},
  {title: '名称', key: 'name'},
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {size: 'small', onClick: () => handleEdit(row)}, {default: () => '编辑'}),
          h(NButton, {size: 'small', type: 'error', onClick: () => handleDelete(row)}, {default: () => '删除'})
        ]
      })
    }
  }
]

// 表单配置
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      {name: 'name', label: '名称', type: 'input', required: true, maxlength: 100},
      {name: 'description', label: '描述', type: 'textarea', maxlength: 500},
      {name: 'is_active', label: '启用', type: 'switch', checkedValue: true, uncheckedValue: false}
    ]
  }
])

// 验证规则
const formRules = (model) => ({
  name: [{required: true, message: '请输入名称', trigger: ['blur', 'input']}]
})

// 方法
const loadResources = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/resource', {
      params: {page: pagination.page, page_size: pagination.pageSize, search: searchKeyword.value}
    })
    data.value = result.items || []
    pagination.itemCount = result.total
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = {...defaultFormData}
  showDialog.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = {...row}
  showDialog.value = true
}

const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除 "${row.name}" 吗？`,
    onPositiveClick: async () => {
      await window.$request.delete(`/resource/${row.id}`)
      window.$message.success('删除成功')
      loadResources()
    }
  })
}

const handleSubmit = async (data) => {
  if (dialogType.value === 'add') {
    await window.$request.post('/resource', data)
  } else {
    await window.$request.put(`/resource/${data.id}`, data)
  }
  window.$message.success('保存成功')
  showDialog.value = false
  loadResources()
}

onMounted(() => loadResources())
</script>
```

**规范要点：**
- 使用 `<script setup>` 语法
- 使用 `window.$request` 调用 API
- 使用 `window.$message` 显示消息
- 使用 `window.$dialog` 确认操作
- 使用 `DialogForm` 组件

### 2.3 全局方法

```javascript
// 请求
const data = await window.$request.get('/api/resource')
await window.$request.post('/api/resource', formData)

// 消息
window.$message.success('操作成功')
window.$message.error('操作失败')

// 对话框
window.$dialog.warning({
  title: '确认删除',
  content: '确定要删除吗？',
  onPositiveClick: async () => { /* 删除逻辑 */ }
})
```

### 2.4 DialogForm 组件

```javascript
// 字段分组
const fieldGroups = computed(() => [
  {
    title: '基本信息',
    fields: [
      {name: 'name', label: '名称', type: 'input', required: true},
      {name: 'email', label: '邮箱', type: 'input', required: true}
    ]
  }
])

// 验证规则
const formRules = (model) => ({
  name: [{required: true, message: '请输入名称', trigger: ['blur', 'input']}],
  confirmPassword: [
    {
      validator: (rule, value) => value === model.password ? true : new Error('两次密码不一致'),
      trigger: ['blur']
    }
  ]
})
```

---

## 三、代码注释规范

### 3.1 后端注释

```python
class ResourceService:
    """资源服务类"""
    
    def create(self, data: schemas.ResourceCreate) -> Dict[str, Any]:
        """
        创建资源
        
        Args:
            data: 创建数据
        
        Returns:
            创建后的资源数据
        
        Raises:
            ValueError: 参数验证失败
        """
        pass
```

### 3.2 前端注释

```javascript
/**
 * 加载资源列表
 */
const loadResources = async () => {
  // ...
}
```

---

## 四、最佳实践

### 4.1 后端

- **依赖注入**：使用 `Depends(get_engine)`
- **异常处理**：捕获 `ValueError`、`NotFoundException`、`Exception`
- **QueryBuilder**：使用 `QueryBuilder` 进行复杂查询
- **数据脱敏**：对外 API 使用脱敏 Schema
- **批量操作**：使用 `delete_many`、`update_many`

### 4.2 前端

- **全局方法**：优先使用 `window.$request`、`window.$message`、`window.$dialog`
- **错误处理**：利用自动错误提示，无需手动处理
- **表单验证**：使用函数形式的 `formRules(model)` 实现字段联动
- **数据初始化**：使用 `defaultFormData` 避免引用问题

---

## 五、AI 开发提示词模板

### 5.1 后端模块开发提示词

```markdown
你是一个经验丰富的 Python 后端开发工程师。请为 ToolsPlus 项目开发一个 [模块名称] 模块。

项目信息：
- 框架：FastAPI 0.128
- ORM：SQLAlchemy 2.0（Table 定义）
- 数据库：SQLite
- 响应格式：BaseResponse

参考模块：backend/app/modules/acme

请按以下结构创建文件：
1. models.py - 使用 Table 定义数据模型
2. schemas.py - Pydantic v2 模式（Base → Create/Update → Read）
3. repository.py - 数据访问层
4. services.py - 业务逻辑层
5. api.py - FastAPI 路由（必须包含 prefix 和 tags）

规范要求：
- 所有表必须包含 created_at 和 updated_at 字段
- 使用 BaseResponse.success/error 包装响应
- 使用依赖注入 get_engine
- 添加详细的中文注释

功能需求：
[描述具体功能需求]
```

### 5.2 前端组件开发提示词

```markdown
你是一个经验丰富的 Vue 3 前端开发工程师。请为 ToolsPlus 项目开发一个 [组件名称] 组件。

项目信息：
- 框架：Vue 3.4 + Vite 5.0
- UI 库：Naive UI 2.43
- 状态管理：Pinia 3.0
- 代码风格：Composition API + <script setup>

参考组件：frontend/src/modules/ssl/DNS.vue

全局方法：
- window.$request - 请求工具
- window.$message - 消息提示
- window.$dialog - 对话框

规范要求：
- 使用 DialogForm 组件处理表单
- 使用 window.$request 调用 API
- 使用 computed 配置 fieldGroups
- 添加详细的中文注释

功能需求：
[描述具体功能需求]
```

---

## 六、代码生成检查清单

### 6.1 后端检查清单

- [ ] 模块结构完整（api.py、models.py、schemas.py、services.py）
- [ ] 路由包含 prefix 和 tags
- [ ] 使用 BaseResponse 包装响应
- [ ] 使用依赖注入 get_engine
- [ ] 数据模型使用 Table 定义
- [ ] 所有表包含 created_at 和 updated_at
- [ ] Schema 层次：Base → Create/Update → Read
- [ ] 使用 Pydantic v2 语法（ConfigDict）
- [ ] Field 使用正确（必填、可选、默认值）
- [ ] 添加详细的中文注释

### 6.2 前端检查清单

- [ ] 使用 \<script setup\> 语法
- [ ] 使用 window.$request 调用 API
- [ ] 使用 window.$message 显示消息
- [ ] 使用 window.$dialog 确认操作
- [ ] 使用 DialogForm 组件
- [ ] 使用 computed 配置 fieldGroups
- [ ] 验证规则使用函数形式（支持字段联动）
- [ ] 使用 defaultFormData 初始化表单
- [ ] 添加详细的中文注释

---
