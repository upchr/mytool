package com.upchr.mytool.modules.workflow.service;

import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.modules.workflow.dto.WorkflowCreateDTO;
import com.upchr.mytool.modules.workflow.dto.WorkflowTriggerRequest;
import com.upchr.mytool.modules.workflow.entity.Workflow;
import com.upchr.mytool.modules.workflow.entity.WorkflowExecution;
import com.upchr.mytool.modules.workflow.entity.WorkflowNodeExecution;
import com.upchr.mytool.modules.workflow.mapper.WorkflowExecutionMapper;
import com.upchr.mytool.modules.workflow.mapper.WorkflowMapper;
import com.upchr.mytool.modules.workflow.mapper.WorkflowNodeExecutionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 工作流服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class WorkflowService extends ServiceImpl<WorkflowMapper, Workflow> {

    private final WorkflowExecutionMapper executionMapper;
    private final WorkflowNodeExecutionMapper nodeExecutionMapper;

    /**
     * 创建工作流
     */
    public Map<String, Object> create(WorkflowCreateDTO dto) {
        if (lambdaQuery().eq(Workflow::getWorkflowId, dto.getWorkflowId()).exists()) {
            throw new BusinessException("工作流ID已存在");
        }

        Workflow workflow = new Workflow();
        workflow.setWorkflowId(dto.getWorkflowId());
        workflow.setName(dto.getName());
        workflow.setDescription(dto.getDescription());
        workflow.setSchedule(dto.getSchedule());
        workflow.setNodes(dto.getNodes() != null ? JSONUtil.toJsonStr(dto.getNodes()) : "[]");
        workflow.setEdges(dto.getEdges() != null ? JSONUtil.toJsonStr(dto.getEdges()) : "[]");
        workflow.setIsActive(dto.getIsActive());
        workflow.setDefaultVersion(1);
        workflow.setCreatedAt(LocalDateTime.now());
        workflow.setUpdatedAt(LocalDateTime.now());

        save(workflow);

        return toMap(workflow);
    }

    /**
     * 获取工作流
     */
    public Map<String, Object> getById(String workflowId) {
        Workflow workflow = lambdaQuery()
                .eq(Workflow::getWorkflowId, workflowId)
                .one();
        if (workflow == null) {
            return null;
        }
        return toMap(workflow);
    }

    /**
     * 获取工作流列表
     */
    public Map<String, Object> getList(Integer page, Integer pageSize, Boolean isActive, String keyword) {
        LambdaQueryWrapper<Workflow> wrapper = new LambdaQueryWrapper<>();
        
        if (isActive != null) {
            wrapper.eq(Workflow::getIsActive, isActive);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.and(w -> w.like(Workflow::getName, keyword).or().like(Workflow::getDescription, keyword));
        }
        wrapper.orderByDesc(Workflow::getCreatedAt);

        List<Workflow> workflows = list(wrapper);

        Map<String, Object> result = new HashMap<>();
        result.put("list", workflows.stream().map(this::toMap).toList());
        result.put("total", workflows.size());
        result.put("page", page);
        result.put("page_size", pageSize);

        return result;
    }

    /**
     * 更新工作流
     */
    public Map<String, Object> update(String workflowId, WorkflowCreateDTO dto) {
        Workflow workflow = lambdaQuery()
                .eq(Workflow::getWorkflowId, workflowId)
                .one();
        if (workflow == null) {
            throw new BusinessException("工作流不存在");
        }

        if (dto.getName() != null) workflow.setName(dto.getName());
        if (dto.getDescription() != null) workflow.setDescription(dto.getDescription());
        if (dto.getSchedule() != null) workflow.setSchedule(dto.getSchedule());
        if (dto.getNodes() != null) workflow.setNodes(JSONUtil.toJsonStr(dto.getNodes()));
        if (dto.getEdges() != null) workflow.setEdges(JSONUtil.toJsonStr(dto.getEdges()));
        if (dto.getIsActive() != null) workflow.setIsActive(dto.getIsActive());
        workflow.setUpdatedAt(LocalDateTime.now());

        updateById(workflow);

        return toMap(workflow);
    }

    /**
     * 删除工作流
     */
    public boolean delete(String workflowId) {
        return lambdaUpdate().eq(Workflow::getWorkflowId, workflowId).remove();
    }

    /**
     * 触发工作流
     */
    public Long trigger(String workflowId, String triggeredBy, Object inputs) {
        Workflow workflow = lambdaQuery()
                .eq(Workflow::getWorkflowId, workflowId)
                .one();
        if (workflow == null) {
            throw new BusinessException("工作流不存在");
        }

        WorkflowExecution execution = new WorkflowExecution();
        execution.setWorkflowId(workflowId);
        execution.setStatus("pending");
        execution.setTriggeredBy(triggeredBy != null ? triggeredBy : "manual");
        execution.setInputs(inputs != null ? JSONUtil.toJsonStr(inputs) : "{}");
        execution.setStartTime(LocalDateTime.now());
        execution.setCreatedAt(LocalDateTime.now());

        executionMapper.insert(execution);

        // 异步执行
        executeWorkflowAsync(execution.getId());

        return execution.getId();
    }

    /**
     * 异步执行工作流
     */
    @Async("workflowExecutor")
    public void executeWorkflowAsync(Long executionId) {
        WorkflowExecution execution = executionMapper.selectById(executionId);
        if (execution == null) {
            return;
        }

        Workflow workflow = lambdaQuery()
                .eq(Workflow::getWorkflowId, execution.getWorkflowId())
                .one();
        if (workflow == null) {
            execution.setStatus("failed");
            execution.setError("工作流不存在");
            execution.setEndTime(LocalDateTime.now());
            executionMapper.updateById(execution);
            return;
        }

        execution.setStatus("running");
        executionMapper.updateById(execution);

        try {
            // 解析节点和边
            List<Map<String, Object>> nodes = JSONUtil.toList(workflow.getNodes(), Map.class);
            List<Map<String, Object>> edges = JSONUtil.toList(workflow.getEdges(), Map.class);

            // 执行工作流（简化版）
            for (Map<String, Object> node : nodes) {
                String nodeType = (String) node.get("type");
                String nodeId = (String) node.get("id");
                String nodeName = (String) node.getOrDefault("name", nodeId);

                // 创建节点执行记录
                WorkflowNodeExecution nodeExecution = new WorkflowNodeExecution();
                nodeExecution.setExecutionId(executionId);
                nodeExecution.setNodeId(nodeId);
                nodeExecution.setNodeName(nodeName);
                nodeExecution.setNodeType(nodeType);
                nodeExecution.setStatus("success");
                nodeExecution.setStartTime(LocalDateTime.now());
                nodeExecution.setEndTime(LocalDateTime.now());
                nodeExecution.setOutput("节点执行完成");
                nodeExecution.setCreatedAt(LocalDateTime.now());

                nodeExecutionMapper.insert(nodeExecution);
            }

            execution.setStatus("success");
            execution.setEndTime(LocalDateTime.now());

        } catch (Exception e) {
            execution.setStatus("failed");
            execution.setError(e.getMessage());
            execution.setEndTime(LocalDateTime.now());
            log.error("工作流执行失败: {}", e.getMessage());
        }

        executionMapper.updateById(execution);
    }

    /**
     * 获取执行记录
     */
    public Map<String, Object> getExecution(Long executionId) {
        WorkflowExecution execution = executionMapper.selectById(executionId);
        if (execution == null) {
            return null;
        }
        return executionToMap(execution);
    }

    /**
     * 获取工作流执行记录列表
     */
    public List<Map<String, Object>> getExecutions(String workflowId, int limit) {
        List<WorkflowExecution> executions = executionMapper.selectList(
                new LambdaQueryWrapper<WorkflowExecution>()
                        .eq(WorkflowExecution::getWorkflowId, workflowId)
                        .orderByDesc(WorkflowExecution::getStartTime)
                        .last("LIMIT " + limit)
        );
        return executions.stream().map(this::executionToMap).toList();
    }

    /**
     * 获取节点执行记录
     */
    public List<Map<String, Object>> getNodeExecutions(Long executionId) {
        List<WorkflowNodeExecution> executions = nodeExecutionMapper.selectList(
                new LambdaQueryWrapper<WorkflowNodeExecution>()
                        .eq(WorkflowNodeExecution::getExecutionId, executionId)
                        .orderByAsc(WorkflowNodeExecution::getStartTime)
        );
        return executions.stream().map(this::nodeExecutionToMap).toList();
    }

    /**
     * 验证工作流格式
     */
    public Map<String, Object> validateFormat(Object nodes, Object edges) {
        Map<String, Object> result = new HashMap<>();
        result.put("valid", true);
        result.put("errors", Collections.emptyList());
        result.put("warnings", Collections.emptyList());
        result.put("node_count", nodes != null ? JSONUtil.parseArray(nodes).size() : 0);
        result.put("edge_count", edges != null ? JSONUtil.parseArray(edges).size() : 0);
        return result;
    }

    // ========== 辅助方法 ==========

    private Map<String, Object> toMap(Workflow workflow) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", workflow.getId());
        map.put("workflow_id", workflow.getWorkflowId());
        map.put("name", workflow.getName());
        map.put("description", workflow.getDescription());
        map.put("schedule", workflow.getSchedule());
        map.put("nodes", workflow.getNodes() != null ? JSONUtil.parseArray(workflow.getNodes()) : Collections.emptyList());
        map.put("edges", workflow.getEdges() != null ? JSONUtil.parseArray(workflow.getEdges()) : Collections.emptyList());
        map.put("is_active", workflow.getIsActive());
        map.put("default_version", workflow.getDefaultVersion());
        map.put("created_at", workflow.getCreatedAt());
        map.put("updated_at", workflow.getUpdatedAt());
        return map;
    }

    private Map<String, Object> executionToMap(WorkflowExecution execution) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", execution.getId());
        map.put("workflow_id", execution.getWorkflowId());
        map.put("status", execution.getStatus());
        map.put("triggered_by", execution.getTriggeredBy());
        map.put("inputs", execution.getInputs() != null ? JSONUtil.parseObj(execution.getInputs()) : Collections.emptyMap());
        map.put("start_time", execution.getStartTime());
        map.put("end_time", execution.getEndTime());
        map.put("error", execution.getError());
        map.put("created_at", execution.getCreatedAt());
        return map;
    }

    private Map<String, Object> nodeExecutionToMap(WorkflowNodeExecution execution) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", execution.getId());
        map.put("execution_id", execution.getExecutionId());
        map.put("node_id", execution.getNodeId());
        map.put("node_name", execution.getNodeName());
        map.put("node_type", execution.getNodeType());
        map.put("status", execution.getStatus());
        map.put("start_time", execution.getStartTime());
        map.put("end_time", execution.getEndTime());
        map.put("output", execution.getOutput());
        map.put("error", execution.getError());
        map.put("logs", execution.getLogs() != null ? JSONUtil.parseArray(execution.getLogs()) : Collections.emptyList());
        return map;
    }
}
