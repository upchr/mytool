/**
 * 任务模板 API 接口
 */
import request from '@/utils/request'

const BASE_URL = '/task-templates'

export const taskTemplateApi = {
  /**
   * 获取模板列表
   */
  list(params) {
    return request.get(BASE_URL, { params })
  },

  /**
   * 获取模板详情
   */
  get(templateId) {
    return request.get(`${BASE_URL}/${templateId}`)
  },

  /**
   * 创建模板
   */
  create(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新模板
   */
  update(templateId, data) {
    return request.put(`${BASE_URL}/${templateId}`, data)
  },

  /**
   * 删除模板
   */
  delete(templateId) {
    return request.delete(`${BASE_URL}/${templateId}`)
  },

  /**
   * 应用模板
   */
  apply(templateId, data) {
    return request.post(`${BASE_URL}/${templateId}/apply`, data)
  },

  /**
   * 获取分类列表
   */
  getCategories() {
    return request.get(`${BASE_URL}/categories`)
  }
}

export default taskTemplateApi
