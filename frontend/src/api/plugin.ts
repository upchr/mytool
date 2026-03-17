import { request } from '../utils/request';

export interface Plugin {
  id: number;
  plugin_id: string;
  name: string;
  version: string;
  author: string;
  description?: string;
  plugin_type: string;
  category?: string;
  entry_point: string;
  permissions: string[];
  icon?: string;
  homepage?: string;
  repository?: string;
  license?: string;
  is_official: boolean;
  is_enabled: boolean;
  is_installed: boolean;
  download_count: number;
  rating_count: number;
  rating_avg: number;
  installed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PluginConfig {
  id: number;
  plugin_id: string;
  config_key: string;
  config_value?: string;
  config_type: string;
  is_secret: boolean;
  created_at: string;
  updated_at: string;
}

export interface PluginQueryParams {
  plugin_type?: string;
  category?: string;
  is_official?: boolean;
  is_installed?: boolean;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface PluginInstallRequest {
  plugin_id: string;
  config: Record<string, any>;
}

export interface PluginCallRequest {
  plugin_id: string;
  method: string;
  params: Record<string, any>;
}

/**
 * 获取插件列表
 */
export function listPlugins(params?: PluginQueryParams) {
  return request.get<Plugin[]>('/plugins', { params });
}

/**
 * 获取插件详情
 */
export function getPlugin(pluginId: string) {
  return request.get<Plugin>(`/plugins/${pluginId}`);
}

/**
 * 安装插件
 */
export function installPlugin(data: PluginInstallRequest) {
  return request.post(`/plugins/${data.plugin_id}/install`, data);
}

/**
 * 卸载插件
 */
export function uninstallPlugin(pluginId: string) {
  return request.post(`/plugins/${pluginId}/uninstall`);
}

/**
 * 加载插件
 */
export function loadPlugin(pluginId: string) {
  return request.post(`/plugins/${pluginId}/load`);
}

/**
 * 调用插件方法
 */
export function callPlugin(data: PluginCallRequest) {
  return request.post('/plugins/call', data);
}

/**
 * 获取插件配置
 */
export function getPluginConfigs(pluginId: string) {
  return request.get<PluginConfig[]>(`/plugins/${pluginId}/configs`);
}

/**
 * 设置插件配置
 */
export function setPluginConfig(pluginId: string, config: { config_key: string; config_value?: string; config_type?: string; is_secret?: boolean }) {
  return request.post<PluginConfig>(`/plugins/${pluginId}/configs`, { plugin_id: pluginId, ...config });
}

/**
 * 给插件评分
 */
export function ratePlugin(pluginId: string, rating: number, comment?: string) {
  return request.post(`/plugins/${pluginId}/ratings`, {
    plugin_id: pluginId,
    user_id: 1,
    rating,
    comment
  });
}
