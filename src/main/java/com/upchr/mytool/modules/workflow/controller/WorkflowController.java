package com.upchr.mytool.modules.workflow.controller;

import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.workflow.dto.WorkflowCreateDTO;
import com.upchr.mytool.modules.workflow.dto.WorkflowTriggerRequest;
import com.upchr.mytool.modules.workflow.service.WorkflowService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 工作流控制器
 */
@Tag(name = "工作流管理")
@RestController
@RequestMapping("/workflows")
@RequiredArgsConstructor
public class WorkflowController {

    private final WorkflowService workflowService;

    @PostMapping
    public BaseResponse<Map<String, Object>> create(@RequestBody WorkflowCreateDTO dto) {
        return BaseResponse.success(workflowService.create(dto));
    }

    @GetMapping
    public BaseResponse<Map<String, Object>> list(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "20") Integer pageSize,
            @RequestParam(required = false) Boolean isActive,
            @RequestParam(required = false) String keyword) {
        return BaseResponse.success(workflowService.getList(page, pageSize, isActive, keyword));
    }

    @GetMapping("/{workflowId}")
    public BaseResponse<Map<String, Object>> getById(@PathVariable String workflowId) {
        Map<String, Object> workflow = workflowService.getById(workflowId);
        if (workflow == null) {
            throw new BusinessException("工作流不存在");
        }
        return BaseResponse.success(workflow);
    }

    @PutMapping("/{workflowId}")
    public BaseResponse<Map<String, Object>> update(@PathVariable String workflowId, @RequestBody WorkflowCreateDTO dto) {
        return BaseResponse.success(workflowService.update(workflowId, dto));
    }

    @DeleteMapping("/{workflowId}")
    public BaseResponse<Void> delete(@PathVariable String workflowId) {
        if (!workflowService.delete(workflowId)) {
            throw new BusinessException("工作流不存在");
        }
        return BaseResponse.success();
    }

    @PostMapping("/trigger")
    public BaseResponse<Map<String, Object>> trigger(@RequestBody WorkflowTriggerRequest request) {
        Long executionId = workflowService.trigger(request.getWorkflowId(), "manual", request.getInputs());
        Map<String, Object> data = new HashMap<>();
        data.put("execution_id", executionId);
        return BaseResponse.success(data);
    }

    @GetMapping("/executions/{executionId}")
    public BaseResponse<Map<String, Object>> getExecution(@PathVariable Long executionId) {
        Map<String, Object> execution = workflowService.getExecution(executionId);
        if (execution == null) {
            throw new BusinessException("执行记录不存在");
        }
        return BaseResponse.success(execution);
    }

    @GetMapping("/executions/{executionId}/nodes")
    public BaseResponse<List<Map<String, Object>>> getNodeExecutions(@PathVariable Long executionId) {
        return BaseResponse.success(workflowService.getNodeExecutions(executionId));
    }

    @PostMapping("/validate")
    public BaseResponse<Map<String, Object>> validate(@RequestBody(required = false) WorkflowCreateDTO dto) {
        return BaseResponse.success(workflowService.validateFormat(
                dto != null ? dto.getNodes() : null,
                dto != null ? dto.getEdges() : null
        ));
    }

    @GetMapping("/{workflowId}/executions")
    public BaseResponse<List<Map<String, Object>>> getExecutions(
            @PathVariable String workflowId,
            @RequestParam(defaultValue = "20") Integer limit) {
        return BaseResponse.success(workflowService.getExecutions(workflowId, limit));
    }
}
