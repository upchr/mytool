package com.upchr.mytool.modules.workflow.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 工作流执行记录
 */
@Data
@TableName("workflow_executions")
public class WorkflowExecution {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("workflow_id")
    private String workflowId;

    private String status;

    @TableField("triggered_by")
    private String triggeredBy;

    private String inputs;  // JSON

    @TableField("start_time")
    private LocalDateTime startTime;

    @TableField("end_time")
    private LocalDateTime endTime;

    private String error;

    @TableField("created_at")
    private LocalDateTime createdAt;
}
