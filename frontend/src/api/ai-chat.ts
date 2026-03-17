// AI 配置接口
export interface AIConfig {
  id?: number
  api_key?: string
  api_base?: string
  model?: string
  is_enabled?: boolean
  created_at?: string
  updated_at?: string
}

// 获取 AI 配置列表
export const getAIConfigList = async () => {
  return window.$request.get('/ai-chat/config/list')
}

// 获取 AI 配置详情
export const getAIConfigDetail = async (configId: number = 1) => {
  return window.$request.get(`/ai-chat/config/detail?config_id=${configId}`)
}

// 保存 AI 配置
export const saveAIConfig = async (configId: number, config: AIConfig) => {
  return window.$request.post(`/ai-chat/config/${configId}`, config)
}

// 创建 AI 配置
export const createAIConfig = async (config: AIConfig) => {
  return window.$request.post('/ai-chat/config/create', config)
}

// 删除 AI 配置
export const deleteAIConfig = async (configId: number) => {
  return window.$request.delete(`/ai-chat/config/${configId}`)
}

// 设置激活的 AI 配置
export const setActiveAIConfig = async (configId: number) => {
  return window.$request.post(`/ai-chat/config/${configId}/set-active`)
}

// 获取 AI 配置状态
export const getAIConfigStatus = async () => {
  return window.$request.get('/ai-chat/config')
}

// AI 聊天接口
export interface ChatMessage {
  role: string
  content: string
  timestamp?: number
}

export interface ChatRequest {
  message: string
  history?: ChatMessage[]
  conversation_id?: number
}

// 发送聊天消息（非流式）
export const sendChatMessage = async (data: ChatRequest) => {
  return window.$request.post('/ai-chat/chat', data)
}

// 对话管理接口
export interface Conversation {
  id: number
  title: string
  user_id?: number
  created_at?: string
  updated_at?: string
  messages?: ChatMessage[]
}

export interface ConversationCreate {
  title?: string
}

// 获取对话列表
export const getConversations = async () => {
  return window.$request.get('/ai-chat/conversations')
}

// 创建对话
export const createConversation = async (data?: ConversationCreate) => {
  return window.$request.post('/ai-chat/conversations', data || {})
}

// 获取对话详情
export const getConversation = async (conversationId: number) => {
  return window.$request.get(`/ai-chat/conversations/${conversationId}`)
}

// 删除对话
export const deleteConversation = async (conversationId: number) => {
  return window.$request.delete(`/ai-chat/conversations/${conversationId}`)
}

// 在对话中添加消息
export const createMessage = async (conversationId: number, message: ChatMessage) => {
  return window.$request.post(`/ai-chat/conversations/${conversationId}/messages`, message)
}