// 固定资产管理接口

/**
 * 资产接口定义
 */
export interface Asset {
  id?: number
  name: string  // 资产名称
  category: string  // 资产类别：electronics/home/office/vehicle/other
  price: number  // 购买价格
  purchase_date: string  // 购买日期
  description?: string  // 备注说明
  image_url?: string  // 资产图片URL
  status?: string  // 状态：active/scrapped
  scrapped_date?: string  // 报废日期
  warranty_months?: number  // 质保期（月）
  warranty_expire_date?: string  // 质保到期日期

  // 计算字段
  usage_days?: number  // 使用天数
  daily_cost?: number  // 日均成本
  remaining_warranty_days?: number  // 剩余质保天数
  is_warranty_expired?: boolean  // 质保是否已过期

  created_at?: string
  updated_at?: string
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  pages: number
  items: T[]
}

/**
 * 统计信息
 */
export interface AssetStats {
  total: number  // 总资产数量
  active: number  // 使用中资产
  scrapped: number  // 已报废资产
  total_value: number  // 总资产价值
  daily_cost_sum: number  // 日均成本总和
  by_category: Record<string, { count: number; value: number }>  // 按类别统计
  by_year: Record<number, { count: number; value: number }>  // 按年份统计
}

/**
 * 类别分布
 */
export interface CategoryDistribution {
  category: string
  count: number
  value: number
  percentage: number
}

/**
 * 年度趋势
 */
export interface YearTrend {
  year: number
  count: number
  value: number
}

/**
 * 获取资产列表
 */
export const getAssetList = async (params?: {
  page?: number
  page_size?: number
  category?: string
  status?: string
  search?: string
  sort_by?: string
  sort_order?: string
}) => {
  return window.$request.get('/asset/', { params })
}

/**
 * 获取资产详情
 */
export const getAssetDetail = async (id: number) => {
  return window.$request.get(`/asset/${id}`)
}

/**
 * 创建资产
 */
export const createAsset = async (data: Asset) => {
  return window.$request.post('/asset/', data)
}

/**
 * 更新资产
 */
export const updateAsset = async (id: number, data: Partial<Asset>) => {
  return window.$request.put(`/asset/${id}`, data)
}

/**
 * 删除资产
 */
export const deleteAsset = async (id: number) => {
  return window.$request.delete(`/asset/${id}`)
}

/**
 * 批量删除资产
 */
export const batchDeleteAssets = async (ids: number[]) => {
  return window.$request.post('/asset/batch/delete', { ids })
}

/**
 * 报废资产
 */
export const scrapAsset = async (id: number, scrap_date?: string) => {
  return window.$request.post(`/asset/${id}/scrap`, scrap_date ? { scrap_date } : {})
}

/**
 * 批量报废资产
 */
export const batchScrapAssets = async (ids: number[], scrap_date?: string) => {
  return window.$request.post('/asset/batch/scrap', { ids }, { params: scrap_date ? { scrap_date } : {} })
}

/**
 * 获取统计信息
 */
export const getAssetStats = async () => {
  return window.$request.get('/asset/stats/summary')
}

/**
 * 获取类别分布
 */
export const getCategoryDistribution = async () => {
  return window.$request.get('/asset/stats/category-distribution')
}

/**
 * 获取年度趋势
 */
export const getYearTrend = async (limit?: number) => {
  return window.$request.get('/asset/stats/year-trend', { params: limit ? { limit } : {} })
}

/**
 * 获取价值最高的资产
 */
export const getTopValueAssets = async (limit?: number) => {
  return window.$request.get('/asset/stats/top-value', { params: limit ? { limit } : {} })
}

/**
 * 获取即将过质保的资产
 */
export const getExpiringWarrantyAssets = async (days?: number) => {
  return window.$request.get('/asset/stats/expiring-warranty', { params: days ? { days } : {} })
}

// 资产类别映射
export const CATEGORY_MAP = {
  electronics: '电子产品',
  home: '家居用品',
  office: '办公设备',
  vehicle: '交通工具',
  other: '其他'
}

// 状态映射
export const STATUS_MAP = {
  active: '使用中',
  scrapped: '已报废'
}