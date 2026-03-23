<template>
  <n-card title="固定资产管理" class="asset-page">
    <template #header-extra>
      <n-space :align="isMobile ? 'center' : 'center'" :size="isMobile ? 4 : 8">
        <n-tag type="info" :size="isMobile ? 'tiny' : 'small'">{{ stats.total || 0 }} 个资产</n-tag>
        <n-tag type="success" :size="isMobile ? 'tiny' : 'small'">¥{{ (stats.total_value || 0).toLocaleString() }}</n-tag>
      </n-space>
    </template>

    <!-- 顶部统计卡片 -->
    <n-grid
        :x-gap="isMobile ? 8 : 16"
        :y-gap="isMobile ? 8 : 16"
        :cols="isMobile ? 2 : (isTablet ? 2 : 4)"
        style="margin-bottom: 16px"
        responsive="screen"
    >
      <n-gi>
        <n-statistic label="总资产数量" :value="stats.total || 0">
          <template #prefix>
            <n-icon :size="isMobile ? 16 : 18" color="#2080f0"><CubeOutline /></n-icon>
          </template>
          <template #suffix>
            <span :style="{fontSize: isMobile ? '12px' : '14px', color: '#909399'}">件</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="总资产价值" :value="stats.total_value || 0">
          <template #prefix>
            <n-icon :size="isMobile ? 16 : 18" color="#18a058"><CashOutline /></n-icon>
          </template>
          <template #suffix>
            <span :style="{fontSize: isMobile ? '12px' : '14px', color: '#909399'}">元</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="日均成本总和" :value="stats.daily_cost_sum || 0">
          <template #prefix>
            <n-icon :size="isMobile ? 16 : 18" color="#f0a020"><TrendingUpOutline /></n-icon>
          </template>
          <template #suffix>
            <span :style="{fontSize: isMobile ? '12px' : '14px', color: '#909399'}">元/天</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="已报废资产" :value="stats.scrapped || 0">
          <template #prefix>
            <n-icon :size="isMobile ? 16 : 18" color="#d03050"><TrashOutline /></n-icon>
          </template>
          <template #suffix>
            <span :style="{fontSize: isMobile ? '12px' : '14px', color: '#909399'}">件</span>
          </template>
        </n-statistic>
      </n-gi>
    </n-grid>

    <!-- 图表展示 -->
    <n-space vertical :size="isMobile ? 12 : 16" style="margin-bottom: 16px">
      <n-card size="small" title="资产类别分布">
        <template #header-extra>
          <n-tag type="info" :size="isMobile ? 'tiny' : 'small'">饼图</n-tag>
        </template>
        <n-spin :show="chartLoading">
          <div ref="categoryChartRef" :style="{height: isMobile ? '250px' : '300px'}"></div>
          <n-empty v-if="!chartLoading && !categoryChart" description="暂无数据" :style="{height: isMobile ? '250px' : '300px'}" />
        </n-spin>
      </n-card>
      <n-grid :x-gap="isMobile ? 8 : 16" :cols="isMobile ? 1 : 2">
        <n-gi>
          <n-card size="small" title="年度购买趋势">
            <template #header-extra>
              <n-tag type="info" :size="isMobile ? 'tiny' : 'small'">柱状图</n-tag>
            </template>
            <n-spin :show="chartLoading">
              <div ref="yearTrendChartRef" :style="{height: isMobile ? '250px' : '300px'}"></div>
              <n-empty v-if="!chartLoading && !yearTrendChart" description="暂无数据" :style="{height: isMobile ? '250px' : '300px'}" />
            </n-spin>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small" title="价值排行榜">
            <template #header-extra>
              <n-tag type="warning" :size="isMobile ? 'tiny' : 'small'">TOP 10</n-tag>
            </template>
            <n-spin :show="loading">
              <n-list bordered :style="{maxHeight: isMobile ? '250px' : '300px', overflowY: 'auto'}">
                <n-list-item v-for="(item, index) in topValueAssets" :key="item.id">
                  <template #prefix>
                    <n-tag :type="index < 3 ? 'warning' : 'default'" :bordered="false" :size="isMobile ? 'tiny' : 'small'">
                      {{ index + 1 }}
                    </n-tag>
                  </template>
                  <n-space justify="space-between" style="width: 100%">
                    <n-text :style="{fontSize: isMobile ? '12px' : '14px'}">{{ item.name }}</n-text>
                    <n-text :style="{color: '#f0a020', fontWeight: 'bold', fontSize: isMobile ? '12px' : '14px'}">¥{{ item.price.toLocaleString() }}</n-text>
                  </n-space>
                </n-list-item>
                <n-list-item v-if="topValueAssets.length === 0">
                  <n-empty description="暂无数据" :size="isMobile ? 'small' : 'medium'" />
                </n-list-item>
              </n-list>
            </n-spin>
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>

    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-filters">
        <n-space :vertical="isMobile" :size="isMobile ? 8 : 0" :wrap="true" style="width: 100%">
          <n-input
              v-model:value="searchKeyword"
              placeholder="搜索名称、备注"
              clearable
              :style="{width: isMobile ? '100%' : '200px'}"
              :size="isMobile ? 'medium' : 'small'"
              @keyup.enter="handleSearch"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          <n-select
              v-model:value="filterCategory"
              placeholder="类别筛选"
              clearable
              :style="{width: isMobile ? '100%' : '120px'}"
              :size="isMobile ? 'medium' : 'small'"
              :options="categoryOptions"
              @update:value="loadAssets"
          />
          <n-select
              v-model:value="filterStatus"
              placeholder="状态筛选"
              clearable
              :style="{width: isMobile ? '100%' : '100px'}"
              :size="isMobile ? 'medium' : 'small'"
              :options="statusOptions"
              @update:value="loadAssets"
          />
          <n-button
              quaternary
              :size="isMobile ? 'medium' : 'small'"
              @click="resetFilters"
          >
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            <span v-if="!isMobile">重置</span>
          </n-button>
        </n-space>
      </div>
      <div class="toolbar-actions">
        <n-space :wrap="true" :size="isMobile ? 4 : 0">
          <n-button
              type="primary"
              :size="isMobile ? 'medium' : 'small'"
              @click="handleAdd"
          >
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            添加
          </n-button>
          <n-button
              type="error"
              :size="isMobile ? 'medium' : 'small'"
              @click="deleteAll"
              :disabled="checkedRowKeys.length === 0"
          >
            <template #icon>
              <n-icon><TrashOutline /></n-icon>
            </template>
            <span v-if="!isMobile">批量删除</span>
            <span v-else>({{ checkedRowKeys.length }})</span>
          </n-button>
          <n-button
              type="warning"
              :size="isMobile ? 'medium' : 'small'"
              @click="batchScrap"
              :disabled="checkedRowKeys.length === 0"
          >
            <template #icon>
              <n-icon><StopCircleOutline /></n-icon>
            </template>
            <span v-if="!isMobile">批量报废</span>
            <span v-else>({{ checkedRowKeys.length }})</span>
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 数据表格 -->
    <n-data-table
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        :row-key="row => row.id"
        :scroll-x="isMobile ? 800 : 1400"
        :size="isMobile ? 'small' : 'medium'"
        remote
    />

    <!-- 新增/编辑对话框 -->
    <DialogForm
        ref="dialogRef"
        dialogPreset="card"
        v-model:visible="showDialog"
        v-model:formData="formData"
        :use-field-groups="true"
        :field-groups="fieldGroups"
        :rules="formRules"
        :title="dialogTitle"
        :positive-text="dialogType === 'add' ? '添加' : '更新'"
        :validate-on-submit="true"
        :show-success-message="true"
        success-message="保存成功！"
        @submit="handleSubmit"
    >
      <template #action="{ formData }">
        <n-space justify="end">
          <n-button :size="isMobile ? 'medium' : 'small'" @click="handleCancel">取消</n-button>
          <n-button
              :size="isMobile ? 'medium' : 'small'"
              type="success"
              :loading="submitting"
              @click="handleSubmit(formData, true)"
          >
            确定
          </n-button>
        </n-space>
      </template>
    </DialogForm>
  </n-card>
</template>

<script setup>
import {h, onMounted, ref, reactive, computed, nextTick, onUnmounted, watch} from "vue"
import {useBreakpoints} from '@vueuse/core'
import {NButton, NTag, NSpace, NInput, NSelect, NStatistic, NGrid, NGi, NList, NListItem, NEmpty} from "naive-ui"
import {
  AddOutline,
  TrashOutline,
  SearchOutline,
  StopCircleOutline,
  RefreshOutline,
  CubeOutline,
  CashOutline,
  TrendingUpOutline,
  CreateOutline
} from "@vicons/ionicons5"
import DialogForm from "@/components/DialogForm.vue"
import * as assetApi from "@/api/asset"
import * as echarts from 'echarts'

// 响应式断点
const breakpoints = useBreakpoints({
  mobile: 640,
  tablet: 768,
  laptop: 1024,
  desktop: 1280
})

const isMobile = breakpoints.smaller('mobile')
const isTablet = breakpoints.between('mobile', 'laptop')

// ========== 状态定义 ==========
const loading = ref(false)
const submitting = ref(false)
const data = ref([])
const checkedRowKeys = ref([])
const searchKeyword = ref('')
const filterCategory = ref(null)
const filterStatus = ref(null)
const stats = ref({
  total: 0,
  active: 0,
  scrapped: 0,
  total_value: 0,
  daily_cost_sum: 0,
  by_category: {},
  by_year: {}
})
const topValueAssets = ref([])
const chartLoading = ref(false)

// 图表引用
const categoryChartRef = ref(null)
const yearTrendChartRef = ref(null)
let categoryChart = null
let yearTrendChart = null

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  prefix: ({ itemCount }) => `总共 ${itemCount} 条`,
  onChange: (page) => handlePageChange(page),
  onUpdatePageSize: (pageSize) => handlePageSizeChange(pageSize)
})

// 筛选选项
const categoryOptions = [
  {label: '电子产品', value: 'electronics'},
  {label: '家居用品', value: 'home'},
  {label: '办公设备', value: 'office'},
  {label: '交通工具', value: 'vehicle'},
  {label: '其他', value: 'other'}
]

const statusOptions = [
  {label: '使用中', value: 'active'},
  {label: '已报废', value: 'scrapped'}
]

// ========== 表格列定义 ==========
const columns = [
  {
    type: "selection",
    width: 40
  },
  {
    title: "ID",
    key: "id",
    width: 80,
    sorter: (a, b) => a.id - b.id
  },
  {
    title: "资产名称",
    key: "name",
    width: 150,
    ellipsis: {tooltip: true}
  },
  {
    title: "类别",
    key: "category",
    width: 100,
    render(row) {
      const categoryMap = {
        electronics: {label: '电子产品', color: '#18a058'},
        home: {label: '家居用品', color: '#2080f0'},
        office: {label: '办公设备', color: '#f0a020'},
        vehicle: {label: '交通工具', color: '#d03050'},
        other: {label: '其他', color: '#909399'}
      }
      const info = categoryMap[row.category] || {label: row.category, color: 'default'}
      return h(NTag, {
        type: 'info',
        bordered: false,
        style: {backgroundColor: info.color + '20', color: info.color}
      }, {default: () => info.label})
    }
  },
  {
    title: "购买价格",
    key: "price",
    width: 100,
    render(row) {
      return `¥${row.price.toLocaleString()}`
    }
  },
  {
    title: "购买日期",
    key: "purchase_date",
    width: 120,
    render(row) {
      return new Date(row.purchase_date).toLocaleDateString()
    }
  },
  {
    title: "使用天数",
    key: "usage_days",
    width: 90,
    render(row) {
      return h('span', {
        style: {color: row.usage_days > 365 ? '#18a058' : '#909399'}
      }, `${row.usage_days} 天`)
    }
  },
  {
    title: "日均成本",
    key: "daily_cost",
    width: 100,
    render(row) {
      return h('span', {
        style: {color: '#f0a020', fontWeight: 'bold'}
      }, `¥${row.daily_cost.toFixed(2)}`)
    }
  },
  {
    title: "状态",
    key: "status",
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.status === 'active' ? 'success' : 'default',
        bordered: false
      }, {default: () => row.status === 'active' ? '使用中' : '已报废'})
    }
  },
  {
    title: "质保",
    key: "warranty",
    width: 100,
    render(row) {
      if (!row.warranty_months) return '-'
      if (row.is_warranty_expired) {
        return h(NTag, {type: 'error', bordered: false}, {default: () => '已过期'})
      }
      if (row.remaining_warranty_days && row.remaining_warranty_days <= 30) {
        return h(NTag, {type: 'warning', bordered: false}, {default: () => `${row.remaining_warranty_days}天`})
      }
      return h(NTag, {type: 'success', bordered: false}, {default: () => `${row.remaining_warranty_days}天`})
    }
  },
  {
    title: "备注",
    key: "description",
    width: 150,
    ellipsis: {tooltip: true},
    render(row) {
      return row.description || '-'
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 200,
    render(row) {
      return h(NSpace, {size: 'small'}, {
        default: () => [
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            onClick: () => handleEdit(row)
          }, {
            icon: () => h(CreateOutline),
            default: () => "编辑"
          }),
          row.status === 'active' ? h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "warning",
            onClick: () => handleScrap(row)
          }, {
            icon: () => h(StopCircleOutline),
            default: () => "报废"
          }) : null,
          h(NButton, {
            strong: true,
            tertiary: true,
            size: "small",
            type: "error",
            onClick: () => handleDelete(row)
          }, {
            icon: () => h(TrashOutline),
            default: () => "删除"
          })
        ]
      })
    }
  }
]
// const columns = computed(() => {
//   const allColumns = [
//     {
//       type: "selection",
//       width: 40
//     },
//     {
//       title: "ID",
//       key: "id",
//       width: 80,
//       sorter: (a, b) => a.id - b.id,
//       hidden: isMobile.value
//     },
//     {
//       title: "资产名称",
//       key: "name",
//       width: isMobile.value ? 120 : 150,
//       ellipsis: {tooltip: true}
//     },
//     {
//       title: "类别",
//       key: "category",
//       width: isMobile.value ? 80 : 100,
//       render(row) {
//         const categoryMap = {
//           electronics: {label: '电子产品', color: '#18a058'},
//           home: {label: '家居用品', color: '#2080f0'},
//           office: {label: '办公设备', color: '#f0a020'},
//           vehicle: {label: '交通工具', color: '#d03050'},
//           other: {label: '其他', color: '#909399'}
//         }
//         const info = categoryMap[row.category] || {label: row.category, color: 'default'}
//         return h(NTag, {
//           type: 'info',
//           bordered: false,
//           size: isMobile.value ? 'small' : 'medium',
//           style: {backgroundColor: info.color + '20', color: info.color}
//         }, {default: () => info.label})
//       }
//     },
//     {
//       title: "购买价格",
//       key: "price",
//       width: isMobile.value ? 90 : 100,
//       render(row) {
//         return `¥${row.price.toLocaleString()}`
//       }
//     },
//     {
//       title: "购买日期",
//       key: "purchase_date",
//       width: isMobile.value ? 100 : 120,
//       render(row) {
//         return new Date(row.purchase_date).toLocaleDateString()
//       }
//     },
//     {
//       title: "使用天数",
//       key: "usage_days",
//       width: isMobile.value ? 80 : 90,
//       hidden: isMobile.value,
//       render(row) {
//         return h('span', {
//           style: {color: row.usage_days > 365 ? '#18a058' : '#909399'}
//         }, `${row.usage_days} 天`)
//       }
//     },
//     {
//       title: "日均成本",
//       key: "daily_cost",
//       width: isMobile.value ? 90 : 100,
//       render(row) {
//         return h('span', {
//           style: {color: '#f0a020', fontWeight: 'bold', fontSize: isMobile.value ? '12px' : '14px'}
//         }, `¥${row.daily_cost.toFixed(2)}`)
//       }
//     },
//     {
//       title: "状态",
//       key: "status",
//       width: isMobile.value ? 70 : 80,
//       render(row) {
//         return h(NTag, {
//           type: row.status === 'active' ? 'success' : 'default',
//           bordered: false,
//           size: isMobile.value ? 'small' : 'medium'
//         }, {default: () => row.status === 'active' ? '使用中' : '已报废'})
//       }
//     },
//     {
//       title: "质保",
//       key: "warranty",
//       width: isMobile.value ? 80 : 100,
//       render(row) {
//         if (!row.warranty_months) return '-'
//         if (row.is_warranty_expired) {
//           return h(NTag, {type: 'error', bordered: false, size: isMobile.value ? 'tiny' : 'small'}, {default: () => '已过期'})
//         }
//         if (row.remaining_warranty_days && row.remaining_warranty_days <= 30) {
//           return h(NTag, {type: 'warning', bordered: false, size: isMobile.value ? 'tiny' : 'small'}, {default: () => `${row.remaining_warranty_days}天`})
//         }
//         return h(NTag, {type: 'success', bordered: false, size: isMobile.value ? 'tiny' : 'small'}, {default: () => `${row.remaining_warranty_days}天`})
//       }
//     },
//     {
//       title: "备注",
//       key: "description",
//       width: isMobile.value ? 100 : 150,
//       ellipsis: {tooltip: true},
//       render(row) {
//         return row.description || '-'
//       }
//     },
//     {
//       title: "操作",
//       key: "actions",
//       width: isMobile.value ? 180 : 200,
//       fixed: "right",
//       render(row) {
//         return h(NSpace, {size: isMobile.value ? 'tiny' : 'small'}, {
//           default: () => [
//             h(NButton, {
//               strong: true,
//               tertiary: true,
//               size: isMobile.value ? 'tiny' : 'small',
//               onClick: () => handleEdit(row)
//             }, {
//               icon: () => h(CreateOutline),
//               default: () => isMobile.value ? '' : '编辑'
//             }),
//             row.status === 'active' ? h(NButton, {
//               strong: true,
//               tertiary: true,
//               size: isMobile.value ? 'tiny' : 'small',
//               type: "warning",
//               onClick: () => handleScrap(row)
//             }, {
//               icon: () => h(StopCircleOutline),
//               default: () => isMobile.value ? '' : '报废'
//             }) : null,
//             h(NButton, {
//               strong: true,
//               tertiary: true,
//               size: isMobile.value ? 'tiny' : 'small',
//               type: "error",
//               onClick: () => handleDelete(row)
//             }, {
//               icon: () => h(TrashOutline),
//               default: () => isMobile.value ? '' : '删除'
//             })
//           ]
//         })
//       }
//     }
//   ]
//
//   return allColumns.filter(col => !col.hidden)
// })



// ========== 表单配置 ==========
const dialogRef = ref(null)
const showDialog = ref(false)
const dialogType = ref('add')

const formData = ref({
  name: '',
  category: 'electronics',
  price: 0,
  purchase_date: new Date().getTime(),
  description: '',
  image_url: '',
  warranty_months: 0
})

const defaultFormData = {
  name: '',
  category: 'electronics',
  price: 0,
  purchase_date: new Date().getTime(),
  description: '',
  image_url: '',
  warranty_months: 0
}

const dialogTitle = computed(() => {
  return dialogType.value === 'add' ? '添加固定资产' : `编辑资产: ${formData.value.name || ''}`
})

// 字段分组
const fieldGroups = [
  {
    title: '基本信息',
    fields: [
      {
        name: 'name',
        label: '资产名称',
        type: 'input',
        placeholder: '如 iPhone 17',
        span: 24
      },
      {
        name: 'category',
        label: '资产类别',
        type: 'select',
        placeholder: '请选择或输入类别',
        options: categoryOptions,
        span: 12
      },
      {
        name: 'purchase_date',
        label: '购买日期',
        type: 'date',
        valueFormat: 'yyyy-MM-dd',
        span: 12
      },
      {
        name: 'price',
        label: '购买价格',
        type: 'number',
        placeholder: '请输入价格',
        span: 12,
        props: {
          precision: 2,
          min: 0,
          style: {width: '100%'}
        }
      },
      {
        name: 'warranty_months',
        label: '质保期（月）',
        type: 'number',
        placeholder: '可选',
        span: 12
      }
    ]
  },
  {
    title: '其他信息',
    visible: false,
    fields: [
      // {
      //   name: 'image_url',
      //   label: '图片URL',
      //   type: 'input',
      //   placeholder: '可选',
      //   span: 24
      // },
      {
        name: 'description',
        label: '备注说明',
        type: 'textarea',
        placeholder: '请输入备注信息',
        span: 24,
        autosize: {minRows: 2, maxRows: 4}
      }
    ]
  }
]

// 表单验证规则
const formRules = {
  name: [
    {required: true, message: '请输入资产名称', trigger: ['blur', 'input']},
    {min: 2, message: '名称至少2个字符', trigger: ['blur']}
  ],
  category: [
    {required: true, message: '请选择资产类别', trigger: ['blur', 'change']}
  ],
  price: [
    {required: true, type: 'number',message: '请输入购买价格', trigger: ['blur', 'change']},
    {type: 'number', min: 0.01, message: '价格必须大于0', trigger: ['blur', 'change']}
  ],
  purchase_date: [
    {required: true, type: 'date', message: '请选择购买日期', trigger: ['blur', 'change']}
  ]
}

// ========== API 调用 ==========
const loadAssets = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (filterCategory.value) {
      params.category = filterCategory.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    const res = await assetApi.getAssetList(params)
    data.value = res.items || []
    pagination.itemCount = res.total || 0

  } catch (error) {
    console.error('加载失败:', error)
    window.$message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await assetApi.getAssetStats()
    stats.value = res
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadTopValueAssets = async () => {
  try {
    const res = await assetApi.getTopValueAssets(10)
    topValueAssets.value = res || []
  } catch (error) {
    console.error('加载排行榜失败:', error)
  }
}

const initCharts = async () => {
  chartLoading.value = true
  await nextTick()

  try {
    // 类别分布饼图
    if (categoryChartRef.value) {
      categoryChart = echarts.init(categoryChartRef.value)
      try {
        const distribution = await assetApi.getCategoryDistribution()
        updateCategoryChart(distribution)
      } catch (error) {
        console.error('加载类别分布失败:', error)
      }
    }

    // 年度趋势柱状图
    if (yearTrendChartRef.value) {
      yearTrendChart = echarts.init(yearTrendChartRef.value)
      try {
        const trend = await assetApi.getYearTrend(10)
        updateYearTrendChart(trend)
      } catch (error) {
        console.error('加载年度趋势失败:', error)
      }
    }
  } finally {
    chartLoading.value = false
  }
}

const updateCategoryChart = (data) => {
  if (!categoryChart) return

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}件 ({d}%)'
    },
    legend: {
      orient: isMobile.value ? 'horizontal' : 'vertical',
      right: isMobile ? 'center' : 10,
      top: isMobile ? 'bottom' : 'center',
      textStyle: {
        fontSize: isMobile.value ? 11 : 12
      }
    },
    series: [
      {
        name: '资产类别',
        type: 'pie',
        radius: isMobile.value ? ['30%', '60%'] : ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: isMobile.value,
          position: 'outside',
          fontSize: isMobile.value ? 10 : 12,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: isMobile.value ? 14 : 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: isMobile.value
        },
        data: data.map(item => ({
          name: item.category,
          value: item.count,
          itemStyle: {
            color: {
              electronics: '#18a058',
              home: '#2080f0',
              office: '#f0a020',
              vehicle: '#d03050',
              other: '#909399'
            }[item.category] || '#909399'
          }
        }))
      }
    ]
  }

  categoryChart.setOption(option)
}

const updateYearTrendChart = (data) => {
  if (!yearTrendChart) return

  const sortedData = [...data].sort((a, b) => a.year - b.year)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: isMobile.value ? '5%' : '3%',
      right: isMobile.value ? '5%' : '4%',
      bottom: isMobile.value ? '10%' : '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedData.map(item => item.year),
      axisLabel: {
        rotate: isMobile.value ? 45 : 0,
        fontSize: isMobile.value ? 10 : 12
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left',
        axisLabel: {
          fontSize: isMobile.value ? 10 : 12
        }
      },
      {
        type: 'value',
        name: '金额（元）',
        position: 'right',
        axisLabel: {
          fontSize: isMobile.value ? 10 : 12,
          formatter: (value) => {
            if (value >= 10000) {
              return (value / 10000).toFixed(1) + '万'
            }
            return value
          }
        }
      }
    ],
    series: [
      {
        name: '数量',
        type: 'bar',
        data: sortedData.map(item => item.count),
        itemStyle: {
          color: '#18a058'
        },
        barWidth: isMobile.value ? '40%' : '60%'
      },
      {
        name: '金额',
        type: 'line',
        yAxisIndex: 1,
        data: sortedData.map(item => item.value),
        itemStyle: {
          color: '#f0a020'
        },
        symbolSize: isMobile.value ? 6 : 8
      }
    ]
  }

  yearTrendChart.setOption(option)
}

const addAsset = async () => {
  submitting.value = true
  try {
    await assetApi.createAsset(formData.value)
    window.$message.success('添加成功')
    showDialog.value = false
    loadAssets()
    loadStats()
    initCharts()
    loadTopValueAssets()
  } catch (error) {
    console.error('添加失败:', error)
    window.$message.error(error.response?.data?.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

const updateAsset = async () => {
  submitting.value = true
  try {
    await assetApi.updateAsset(formData.value.id, formData.value)
    window.$message.success('更新成功')
    showDialog.value = false
    loadAssets()
    loadStats()
    initCharts()
    loadTopValueAssets()
  } catch (error) {
    console.error('更新失败:', error)
    window.$message.error(error.response?.data?.message || '更新失败')
  } finally {
    submitting.value = false
  }
}

const deleteAsset = async (id) => {
  try {
    await assetApi.deleteAsset(id)
    window.$message.success('删除成功')
    loadAssets()
    loadStats()
    initCharts()
  } catch (error) {
    console.error('删除失败:', error)
    window.$message.error(error.response?.data?.message || '删除失败')
  }
}

const batchDelete = async (ids) => {
  try {
    await assetApi.batchDeleteAssets(ids)
    window.$message.success(`成功删除 ${ids.length} 个资产`)
    checkedRowKeys.value = []
    loadAssets()
    loadStats()
    initCharts()
  } catch (error) {
    console.error('批量删除失败:', error)
    const errorMsg = error.response?.data?.message || '批量删除失败'
    window.$message.error(`${errorMsg} (共 ${ids.length} 个资产)`)
  }
}

const scrapAsset = async (id) => {
  try {
    await assetApi.scrapAsset(id)
    window.$message.success('资产已报废')
    loadAssets()
    loadStats()
    loadTopValueAssets()
  } catch (error) {
    console.error('报废失败:', error)
    window.$message.error(error.response?.data?.message || '报废失败')
  }
}

const batchScrapAssets = async (ids) => {
  try {
    await assetApi.batchScrapAssets(ids)
    window.$message.success(`成功报废 ${ids.length} 个资产`)
    checkedRowKeys.value = []
    loadAssets()
    loadStats()
    initCharts()
    loadTopValueAssets()
  } catch (error) {
    console.error('批量报废失败:', error)
    const errorMsg = error.response?.data?.message || '批量报废失败'
    window.$message.error(`${errorMsg} (共 ${ids.length} 个资产)`)
  }
}

// ========== 事件处理 ==========
const handleAdd = () => {
  dialogType.value = 'add'
  formData.value = {...defaultFormData}
  showDialog.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  formData.value = {
    ...row,
    purchase_date: row.purchase_date ? new Date(row.purchase_date).toISOString().split('T')[0] : ''
  }
  showDialog.value = true
}

const handleDelete = (row) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `确定要删除 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteAsset(row.id)
    }
  })
}

const handleScrap = (row) => {
  window.$dialog.warning({
    title: '确认报废',
    content: `确定要报废 "${row.name}" 吗？报废后将停止计算日均成本。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await scrapAsset(row.id)
    }
  })
}

const deleteAll = () => {
  if (checkedRowKeys.value.length === 0) {
    window.$message.warning('请先选择要删除的项')
    return
  }

  window.$dialog.warning({
    title: '批量删除',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 个资产吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await batchDelete(checkedRowKeys.value)
    }
  })
}

const batchScrap = () => {
  if (checkedRowKeys.value.length === 0) {
    window.$message.warning('请先选择要报废的项')
    return
  }

  window.$dialog.warning({
    title: '批量报废',
    content: `确定要报废选中的 ${checkedRowKeys.value.length} 个资产吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await batchScrapAssets(checkedRowKeys.value)
    }
  })
}

const handleSearch = () => {
  pagination.page = 1
  loadAssets()
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterCategory.value = null
  filterStatus.value = null
  pagination.page = 1
  loadAssets()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadAssets()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadAssets()
}

const handleCancel = () => {
  showDialog.value = false
  formData.value = {...defaultFormData}
}

const handleSubmit = async (data, validate = false) => {
  if (validate && dialogRef.value) {
    try {
      await dialogRef.value.validate()
    } catch (error) {
      console.log('表单验证失败:', error)
      return
    }
  }

  formData.value = {...data}

  if (dialogType.value === 'add') {
    await addAsset()
  } else {
    await updateAsset()
  }
}

// 监听断点变化，重新渲染图表
watch(isMobile, async () => {
  if (categoryChart) {
    try {
      const distribution = await assetApi.getCategoryDistribution()
      updateCategoryChart(distribution)
    } catch (error) {
      console.error('重新加载类别分布失败:', error)
    }
  }
  if (yearTrendChart) {
    try {
      const trend = await assetApi.getYearTrend(10)
      updateYearTrendChart(trend)
    } catch (error) {
      console.error('重新加载年度趋势失败:', error)
    }
  }
})

// ========== 初始化 ==========
onMounted(async () => {
  await Promise.all([
    loadAssets(),
    loadStats(),
    loadTopValueAssets()
  ])
  // 在数据加载完成后初始化图表
  await initCharts()

  // 监听窗口大小变化，调整图表
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  categoryChart?.dispose()
  yearTrendChart?.dispose()
})

const handleResize = () => {
  categoryChart?.resize()
  yearTrendChart?.resize()
}
</script>

<style scoped>
:deep(.n-statistic .n-statistic-value) {
  font-size: 24px;
  font-weight: bold;
}

/* 工具栏样式 */
.toolbar {
  display: flex;
  flex-direction: row;
  gap: 12px;
  margin-bottom: 16px;
  align-items: flex-start;
}

.toolbar-filters {
  flex: 1;
  min-width: 0;
}

.toolbar-actions {
  flex-shrink: 0;
}

/* 移动端适配 */
@media (max-width: 640px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
  }

  .toolbar-filters,
  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions :deep(.n-space) {
    width: 100%;
  }

  .toolbar-actions :deep(.n-space-item) {
    flex: 1;
  }

  .toolbar-actions :deep(.n-button) {
    width: 100%;
  }

  :deep(.n-statistic .n-statistic-value) {
    font-size: 20px;
  }

  :deep(.n-statistic .n-statistic-label) {
    font-size: 12px;
  }

  :deep(.n-statistic .n-statistic-value__content) {
    font-size: 20px;
  }

  :deep(.n-statistic .n-statistic-value__suffix) {
    font-size: 12px;
  }

  :deep(.n-data-table) {
    font-size: 13px;
  }

  :deep(.n-data-table th) {
    font-size: 12px;
    padding: 8px 6px;
  }

  :deep(.n-data-table td) {
    padding: 8px 6px;
  }

  :deep(.n-card) {
    border-radius: 8px;
  }

  :deep(.n-pagination) {
    flex-wrap: wrap;
  }

  :deep(.n-pagination .n-pagination-item) {
    min-width: 32px;
    height: 32px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  :deep(.n-statistic .n-statistic-value) {
    font-size: 18px;
  }

  :deep(.n-statistic .n-statistic-label) {
    font-size: 11px;
  }

  :deep(.n-statistic .n-statistic-value__content) {
    font-size: 18px;
  }

  :deep(.n-data-table) {
    font-size: 12px;
  }

  :deep(.n-data-table th) {
    font-size: 11px;
    padding: 6px 4px;
  }

  :deep(.n-data-table td) {
    padding: 6px 4px;
  }
}

/* 横屏模式优化 */
@media (max-width: 768px) and (orientation: landscape) {
  .toolbar {
    flex-direction: row;
    align-items: center;
  }

  .toolbar-filters {
    flex: 1;
  }

  .toolbar-actions {
    flex-shrink: 0;
  }

  :deep(.n-grid) {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
  }

  :deep(.n-statistic .n-statistic-value) {
    font-size: 18px;
  }
}
</style>
