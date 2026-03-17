import request from '@/utils/request'

const BASE_URL = '/workflows'

export const workflowApi = {
  list(params) {
    return request.get(BASE_URL, { params })
  },

  get(workflowId) {
    return request.get(`${BASE_URL}/${workflowId}`)
  },

  create(data) {
    return request.post(BASE_URL, data)
  },

  update(workflowId, data) {
    return request.put(`${BASE_URL}/${workflowId}`, data)
  },

  delete(workflowId) {
    return request.delete(`${BASE_URL}/${workflowId}`)
  },

  trigger(data) {
    return request.post(`${BASE_URL}/trigger`, data)
  },

  getExecution(executionId) {
    return request.get(`${BASE_URL}/executions/${executionId}`)
  },

  getWorkflowExecutions(workflowId, limit = 20) {
    return request.get(`${BASE_URL}/${workflowId}/executions`, { params: { limit } })
  },

  getNodeExecutions(executionId) {
    return request.get(`${BASE_URL}/executions/${executionId}/nodes`)
  }
}

export default workflowApi