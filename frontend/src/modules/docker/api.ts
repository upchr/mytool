/**
 * Docker 管理 API 接口
 */

export const dockerApi = {
  // ========== 容器管理 ==========
  
  /**
   * 获取容器列表
   * @param {number} nodeId - 节点ID
   * @param {boolean} all - 是否包含停止的容器
   * @returns {Promise<Array>} 容器列表
   */
  getContainers: (nodeId, all = true) =>
    window.$request.get(`/docker/nodes/${nodeId}/containers`, { params: { all } }),
  
  /**
   * 快速获取容器列表（仅运行中的）
   * @param {number} nodeId - 节点ID
   * @returns {Promise<Array>} 容器列表
   */
  getContainersFast: (nodeId) =>
    window.$request.get(`/docker/nodes/${nodeId}/containers/fast`),
  
  /**
   * 容器操作（同步）
   * @param {number} nodeId - 节点ID
   * @param {string} containerId - 容器ID
   * @param {string} action - 操作类型：start/stop/restart/remove
   * @returns {Promise<Object>} 操作结果
   */
  containerAction: (nodeId, containerId, action) =>
    window.$request.post(`/docker/nodes/${nodeId}/containers/action`, {
      action,
      container_id: containerId
    }),
  
  /**
   * 容器操作（异步）
   * @param {number} nodeId - 节点ID
   * @param {string} containerId - 容器ID
   * @param {string} action - 操作类型：start/stop/restart/remove
   * @returns {Promise<Object>} 操作结果
   */
  containerActionAsync: (nodeId, containerId, action) =>
    window.$request.post(`/docker/nodes/${nodeId}/containers/action/async`, {
      action,
      container_id: containerId
    }),
  
  /**
   * 获取容器日志
   * @param {number} nodeId - 节点ID
   * @param {string} containerId - 容器ID
   * @param {number} tail - 显示最后N行日志
   * @returns {Promise<Object>} 日志内容
   */
  getContainerLogs: (nodeId, containerId, tail = 100) =>
    window.$request.get(`/docker/nodes/${nodeId}/containers/${containerId}/logs`, { params: { tail } }),
  
  // ========== Compose 项目管理 ==========
  
  /**
   * 获取 Compose 项目列表（快速版）
   * @param {number} nodeId - 节点ID
   * @returns {Promise<Array>} 项目列表
   */
  getComposeProjects: (nodeId) =>
    window.$request.get(`/docker/nodes/${nodeId}/compose`),
  
  /**
   * 获取 Compose 项目列表（包含目录搜索）
   * @param {number} nodeId - 节点ID
   * @returns {Promise<Array>} 项目列表
   */
  getComposeProjectsWithSearch: (nodeId) =>
    window.$request.get(`/docker/nodes/${nodeId}/compose/search`),
  
  /**
   * 读取 Compose 文件内容
   * @param {number} nodeId - 节点ID
   * @param {string} path - 项目路径
   * @returns {Promise<Object>} 文件内容
   */
  getComposeFile: (nodeId, path) =>
    window.$request.get(`/docker/nodes/${nodeId}/compose/file`, { params: { path } }),
  
  /**
   * 保存 Compose 文件
   * @param {number} nodeId - 节点ID
   * @param {string} path - 项目路径
   * @param {string} content - YAML 内容
   * @returns {Promise<Object>} 保存结果
   */
  saveComposeFile: (nodeId, path, content) =>
    window.$request.post(`/docker/nodes/${nodeId}/compose/file`, {
      path,
      content
    }),
  
  /**
   * Compose 项目操作
   * @param {number} nodeId - 节点ID
   * @param {string} path - 项目路径
   * @param {string} action - 操作类型：up/down/restart/pull
   * @param {Array<string>} services - 指定服务列表（可选）
   * @returns {Promise<Object>} 操作结果
   */
  composeAction: (nodeId, path, action, services = null) =>
    window.$request.post(`/docker/nodes/${nodeId}/compose/action`, {
      action,
      path,
      services
    }),
  
  // ========== 操作日志 ==========
  
  /**
   * 获取 Docker 操作日志
   * @param {number} nodeId - 节点ID
   * @param {number} limit - 返回记录数
   * @returns {Promise<Array>} 操作日志列表
   */
  getOperationLogs: (nodeId, limit = 50) =>
    window.$request.get(`/docker/nodes/${nodeId}/logs`, { params: { limit } }),
  
  // ========== WebSocket 工具 ==========
  
  /**
   * 创建容器日志 WebSocket 连接
   * @param {number} nodeId - 节点ID
   * @param {string} containerId - 容器ID
   * @param {number} tail - 显示最后N行日志
   * @param {boolean} follow - 是否实时跟踪
   * @returns {WebSocket} WebSocket 实例
   */
  createLogsWebSocket: (nodeId, containerId, tail = 100, follow = true) => {
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${location.host}/api/docker/nodes/${nodeId}/containers/${containerId}/logs/stream?tail=${tail}&follow=${follow}`
    return new WebSocket(wsUrl)
  },
  
  /**
   * 创建容器终端 WebSocket 连接
   * @param {number} nodeId - 节点ID
   * @param {string} containerId - 容器ID
   * @param {string} shell - Shell 类型（sh/bash/zsh）
   * @returns {WebSocket} WebSocket 实例
   */
  createTerminalWebSocket: (nodeId, containerId, shell = 'sh') => {
    const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${location.host}/api/docker/nodes/${nodeId}/containers/${containerId}/terminal?shell=${shell}`
    return new WebSocket(wsUrl)
  }
}
