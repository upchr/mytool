<template>
  <n-card title="固定资产管理">
    <template #header-extra>
      <n-space align="center">
        <n-tag type="info" size="small">{{ stats.total || 0 }} 个资产</n-tag>
        <n-tag type="success" size="small">¥{{ (stats.total_value || 0).toLocaleString() }}</n-tag>
      </n-space>
    </template>
    
    <!-- 顶部统计卡片 -->
    <n-grid :x-gap="16" :y-gap="16" :cols="4" style="margin-bottom: 16px">
      <n-gi>
        <n-statistic label="总资产数量" :value="stats.total || 0">
          <template #prefix>
            <n-icon size="18" color="#2080f0"><CubeOutline /></n-icon>
          </template>
          <template #suffix>
            <span style="font-size: 14px; color: #909399">件</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="总资产价值" :value="stats.total_value || 0">
          <template #prefix>
            <n-space align="center" :size="4">
              <n-icon size="18" color="#18a058"><CashOutline /></n-icon>
              <span>¥</span>
            </n-space>
          </template>
          <template #suffix>
            <span style="font-size: 14px; color: #909399">元</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="日均成本总和" :value="stats.daily_cost_sum || 0">
          <template #prefix>
            <n-space align="center" :size="4">
              <n-icon size="18" color="#f0a020"><TrendingUpOutline /></n-icon>
              <span>¥</span>
            </n-space>
          </template>
          <template #suffix>
            <span style="font-size: 14px; color: #909399">元/天</span>
          </template>
        </n-statistic>
      </n-gi>
      <n-gi>
        <n-statistic label="已报废资产" :value="stats.scrapped || 0">
          <template #prefix>
            <n-icon size="18" color="#d03050"><TrashOutline /></n-icon>
          </template>
          <template #suffix>
            <span style="font-size: 14px; color: #909399">件</span>
          </template>
        </n-statistic>
      </n-gi>
    </n-grid>

    <!-- 图表展示 -->
    <n-space vertical style="margin-bottom: 16px">
      <n-card size="small" title="资产类别分布">
        <template #header-extra>
          <n-tag type="info" size="small">饼图</n-tag>
        </template>
        <n-spin :show="chartLoading">
          <div ref="categoryChartRef" style="height: 300px"></div>
          <n-empty v-if="!chartLoading && !categoryChart" description="暂无数据" style="height: 300px" />
        </n-spin>
      </n-card>
      <n-grid :x-gap="16" :cols="2">
        <n-gi>
          <n-card size="small" title="年度购买趋势">
            <template #header-extra>
              <n-tag type="info" size="small">柱状图</n-tag>
            </template>
            <n-spin :show="chartLoading">
              <div ref="yearTrendChartRef" style="height: 300px"></div>
              <n-empty v-if="!chartLoading && !yearTrendChart" description="暂无数据" style="height: 300px" />
            </n-spin>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small" title="价值排行榜">
            <template #header-extra>
              <n-tag type="warning" size="small">TOP 10</n-tag>
            </template>
            <n-spin :show="loading">
              <n-list bordered style="max-height: 300px; overflow-y: auto">
                <n-list-item v-for="(item, index) in topValueAssets" :key="item.id">
                  <template #prefix>
                    <n-tag :type="index < 3 ? 'warning' : 'default'" :bordered="false">
                      {{ index + 1 }}
                    </n-tag>
                  </template>
                  <n-space justify="space-between" style="width: 100%">
                    <span>{{ item.name }}</span>
                    <span style="color: #f0a020; font-weight: bold">¥{{ item.price.toLocaleString() }}</span>
                  </n-space>
                </n-list-item>
                <n-list-item v-if="topValueAssets.length === 0">
                  <n-empty description="暂无数据" size="small" />
                </n-list-item>
              </n-list>
            </n-spin>
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>

    <!-- 顶部工具栏 -->
    <n-space justify="space-between" style="margin-bottom: 16px">
      <n-space>
        <n-input
            v-model:value="searchKeyword"
            placeholder="搜索名称、备注"
            clearable
            style="width: 200px"
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
            style="width: 120px"
            :options="categoryOptions"
            @update:value="loadAssets"
        />
        <n-select
            v-model:value="filterStatus"
            placeholder="状态筛选"
            clearable
            style="width: 100px"
            :options="statusOptions"
            @update:value="loadAssets"
        />
        <n-button quaternary @click="resetFilters">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          重置
        </n-button>
      </n-space>
      <n-space>
        <n-button type="primary" @click="handleAdd">
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          添加资产
        </n-button>
        <n-button
            type="error"
            @click="deleteAll"
            :disabled="checkedRowKeys.length === 0"
        >
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          批量删除 ({{ checkedRowKeys.length }})
        </n-button>
        <n-button
            type="warning"
            @click="batchScrap"
            :disabled="checkedRowKeys.length === 0"
        >
          <template #icon>
            <n-icon><StopCircleOutline /></n-icon>
          </template>
          批量报废 ({{ checkedRowKeys.length }})
        </n-button>
      </n-space>
    </n-space>

    <!-- 数据表格 -->
    <n-data-table
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        :row-key="row => row.id"
        :scroll-x="1400"
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
          <n-button size="small" @click="handleCancel">取消</n-button>
          <n-button
              size="small"
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
import {h, onMounted, ref, reactive, computed, nextTick} from "vue"
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
    fixed: "right",
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
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [
      {
        name: '资产类别',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
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
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedData.map(item => item.year),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left'
      },
      {
        type: 'value',
        name: '金额（元）',
        position: 'right'
      }
    ],
    series: [
      {
        name: '数量',
        type: 'bar',
        data: sortedData.map(item => item.count),
        itemStyle: {
          color: '#18a058'
        }
      },
      {
        name: '金额',
        type: 'line',
        yAxisIndex: 1,
        data: sortedData.map(item => item.value),
        itemStyle: {
          color: '#f0a020'
        }
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
  window.addEventListener('resize', () => {
    categoryChart?.resize()
    yearTrendChart?.resize()
  })
})
</script>

<style scoped>
:deep(.n-statistic .n-statistic-value) {
  font-size: 24px;
  font-weight: bold;
}
</style>
