import { request } from '../utils/request';

export interface Node {
  id: number;
  name: string;
  host: string;
  port: number;
  username?: string;
  auth_type?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * 获取节点列表
 */
export function listNodes() {
  return request.get<Node[]>('/nodes');
}

/**
 * 获取单个节点
 */
export function getNode(id: number) {
  return request.get<Node>(`/nodes/${id}`);
}

/**
 * 创建节点
 */
export function createNode(data: Omit<Node, 'id' | 'created_at' | 'updated_at'>) {
  return request.post<Node>('/nodes', data);
}

/**
 * 更新节点
 */
export function updateNode(id: number, data: Partial<Omit<Node, 'id'>>) {
  return request.put<Node>(`/nodes/${id}`, data);
}

/**
 * 删除节点
 */
export function deleteNode(id: number) {
  return request.delete(`/nodes/${id}`);
}
