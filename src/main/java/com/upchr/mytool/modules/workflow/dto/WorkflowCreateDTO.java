package com.upchr.mytool.modules.workflow.dto;

import lombok.Data;

/**
 * 工作流创建 DTO
 */
@Data
public class WorkflowCreateDTO {

    private String workflowId;

    private String name;

    private String description;

    private String schedule;

    private Object nodes;

    private Object edges;

    private Boolean isActive = true;
}
