package com.upchr.mytool.modules.workflow.dto;

import lombok.Data;

/**
 * 工作流触发请求
 */
@Data
public class WorkflowTriggerRequest {

    private String workflowId;

    private Object inputs;
}
