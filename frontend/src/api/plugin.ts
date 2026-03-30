/**
 * 插件 API 接口
 */
import request from '@/utils/request'

const BASE_URL = '/plugins'

export const pluginApi = {
  /**
   * 获取插件列表
   */
  list(params) {
    return request.get(BASE_URL, { params })
  },

  /**
   * 获取插件详情
   */
  get(pluginId) {
    return request.get(`${BASE_URL}/${pluginId}`)
  },

  /**
   * 创建插件
   */
  create(data) {
    return request.post(BASE_URL, data)
  },

  /**
   * 更新插件
   */
  update(pluginId, data) {
    return request.put(`${BASE_URL}/${pluginId}`, data)
  },

  /**
   * 删除插件
   */
  delete(pluginId) {
    return request.delete(`${BASE_URL}/${pluginId}`)
  },

  /**
   * 安装插件
   */
  install(pluginId, config = {}) {
    return request.post(`${BASE_URL}/${pluginId}/install`, config)
  },

  /**
   * 卸载插件
   */
  uninstall(pluginId) {
    return request.post(`${BASE_URL}/${pluginId}/uninstall`)
  },

  /**
   * 获取插件配置
   */
  getConfigs(pluginId) {
    return request.get(`${BASE_URL}/${pluginId}/configs`)
  },

  /**
   * 发送通知（通知类插件）
   */
  send(pluginId, title, content) {
    return request.post(`${BASE_URL}/${pluginId}/send`, { title, content })
  },

  /**
   * 执行命令（执行器类插件）
   */
  execute(pluginId, command, timeout = 300) {
    return request.post(`${BASE_URL}/${pluginId}/execute`, { command, timeout })
  }
}

export default pluginApi
