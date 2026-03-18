/**
 * 工作流 API 接口
 */
import request from '@/utils/request'

const BASE_URL = '/workflows'

export const workflowApi = {
  /**
   * 获取工作流列表
   */
  list(params) {
    return request.get(BASE_URL, { params })
  },

  /**
   * 获取工作流详情
   */
  get(workflowId) {
    return request.get(`${BASE_URL}/${workflowId}`)
  },

  /**
   * 创建工作流
   */
  create(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新工作流
   */
  update(workflowId, data) {
    return request.put(`${BASE_URL}/${workflowId}`, data)
  },

  /**
   * 删除工作流
   */
  delete(workflowId) {
    return request.delete(`${BASE_URL}/${workflowId}`)
  },

  /**
   * 触发工作流执行
   */
  trigger(workflowId, inputs = {}) {
    return request.post(`${BASE_URL}/trigger`, { workflow_id: workflowId, inputs })
  },

  /**
   * 获取执行记录
   */
  getExecution(executionId) {
    return request.get(`${BASE_URL}/executions/${executionId}`)
  },

  /**
   * 获取工作流执行列表
   */
  getWorkflowExecutions(workflowId, limit = 20) {
    return request.get(`${BASE_URL}/${workflowId}/executions`, { params: { limit } })
  },

  /**
   * 获取节点执行记录
   */
  getNodeExecutions(executionId) {
    return request.get(`${BASE_URL}/executions/${executionId}/nodes`)
  },

  /**
   * 创建版本
   */
  createVersion(workflowId, changeNote) {
    return request.post(`${BASE_URL}/${workflowId}/versions`, null, { params: { change_note: changeNote } })
  },

  /**
   * 获取版本列表
   */
  listVersions(workflowId) {
    return request.get(`${BASE_URL}/${workflowId}/versions`)
  },

  /**
   * 获取版本详情
   */
  getVersion(versionId) {
    return request.get(`${BASE_URL}/versions/${versionId}`)
  },

  /**
   * 恢复版本
   */
  restoreVersion(workflowId, versionId, changeNote) {
    return request.post(`${BASE_URL}/${workflowId}/versions/restore`, { 
      version_id: versionId, 
      change_note: changeNote 
    })
  }
}

export default workflowApi
