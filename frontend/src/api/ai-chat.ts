import request from '@/utils/request'
import {getAuthToken} from '@/utils/auth'

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

// 获取 AI 配置详情
export const getAIConfigDetail = async () => {
  const token = getAuthToken()
  return request.get('/ai-chat/config/detail', {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 保存 AI 配置
export const saveAIConfig = async (config: AIConfig) => {
  const token = getAuthToken()
  return request.post('/ai-chat/config', config, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 获取 AI 配置状态
export const getAIConfigStatus = async () => {
  const token = getAuthToken()
  return request.get('/ai-chat/config', {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
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
  const token = getAuthToken()
  return request.post('/ai-chat/chat', data, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
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
  const token = getAuthToken()
  return request.get('/ai-chat/conversations', {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 创建对话
export const createConversation = async (data?: ConversationCreate) => {
  const token = getAuthToken()
  return request.post('/ai-chat/conversations', data || {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 获取对话详情
export const getConversation = async (conversationId: number) => {
  const token = getAuthToken()
  return request.get(`/ai-chat/conversations/${conversationId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 删除对话
export const deleteConversation = async (conversationId: number) => {
  const token = getAuthToken()
  return request.delete(`/ai-chat/conversations/${conversationId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}

// 在对话中添加消息
export const createMessage = async (conversationId: number, message: ChatMessage) => {
  const token = getAuthToken()
  return request.post(`/ai-chat/conversations/${conversationId}/messages`, message, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
}