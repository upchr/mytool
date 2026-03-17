import { request } from '../utils/request';

// ============== 类型定义 ==============

export interface TaskTemplate {
  id: number;
  template_id: string;
  name: string;
  version: string;
  author: string;
  description?: string;
  category: string;
  tags: string[];
  difficulty: string;
  icon?: string;
  is_official: boolean;
  is_enabled: boolean;
  download_count: number;
  rating_count: number;
  rating_avg: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateSchema {
  id: number;
  template_id: string;
  schema_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TemplateScript {
  id: number;
  template_id: string;
  script_type: string;
  script_content: string;
  created_at: string;
  updated_at: string;
}

export interface TemplateCronSuggestion {
  id: number;
  template_id: string;
  label: string;
  cron_value: string;
  is_default: boolean;
  sort_order: number;
}

export interface TaskTemplateDetail extends TaskTemplate {
  schema?: TemplateSchema;
  script?: TemplateScript;
  cron_suggestions: TemplateCronSuggestion[];
}

export interface TemplateImportRequest {
  template_id: string;
  node_id: number;
  config: Record<string, any>;
  schedule?: string;
  name?: string;
}

export interface TemplateQueryParams {
  category?: string;
  tag?: string;
  difficulty?: string;
  is_official?: boolean;
  keyword?: string;
  page?: number;
  page_size?: number;
}

// ============== API 方法 ==============

/**
 * 获取模板列表
 */
export function listTemplates(params?: TemplateQueryParams) {
  return request.get<TaskTemplate[]>('/task-templates', { params });
}

/**
 * 获取模板详情
 */
export function getTemplateDetail(templateId: string) {
  return request.get<TaskTemplateDetail>(`/task-templates/${templateId}`);
}

/**
 * 创建模板
 */
export function createTemplate(data: Omit<TaskTemplate, 'id' | 'download_count' | 'rating_count' | 'rating_avg' | 'created_at' | 'updated_at'>) {
  return request.post<TaskTemplate>('/task-templates', data);
}

/**
 * 更新模板
 */
export function updateTemplate(templateId: string, data: Partial<Omit<TaskTemplate, 'id' | 'template_id'>>) {
  return request.put<TaskTemplate>(`/task-templates/${templateId}`, data);
}

/**
 * 删除模板
 */
export function deleteTemplate(templateId: string) {
  return request.delete(`/task-templates/${templateId}`);
}

/**
 * 一键导入模板
 */
export function importTemplate(data: TemplateImportRequest) {
  return request.post(`/task-templates/${data.template_id}/import`, data);
}

/**
 * 给模板评分
 */
export function rateTemplate(templateId: string, rating: number, comment?: string) {
  return request.post(`/task-templates/${templateId}/ratings`, {
    template_id: templateId,
    user_id: 1, // 临时用户ID
    rating,
    comment
  });
}

/**
 * 获取模板参数配置Schema
 */
export function getTemplateSchema(templateId: string) {
  return request.get<TemplateSchema>(`/task-templates/${templateId}/schema`);
}

/**
 * 获取模板脚本
 */
export function getTemplateScript(templateId: string) {
  return request.get<TemplateScript>(`/task-templates/${templateId}/script`);
}

/**
 * 获取模板Cron建议
 */
export function getTemplateCronSuggestions(templateId: string) {
  return request.get<TemplateCronSuggestion[]>(`/task-templates/${templateId}/cron-suggestions`);
}
