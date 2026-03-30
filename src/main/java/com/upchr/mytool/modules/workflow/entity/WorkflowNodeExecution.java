package com.upchr.mytool.modules.workflow.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 工作流节点执行记录
 */
@Data
@TableName("workflow_node_executions")
public class WorkflowNodeExecution {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("execution_id")
    private Long executionId;

    @TableField("node_id")
    private String nodeId;

    @TableField("node_name")
    private String nodeName;

    @TableField("node_type")
    private String nodeType;

    private String status;

    @TableField("start_time")
    private LocalDateTime startTime;

    @TableField("end_time")
    private LocalDateTime endTime;

    private String output;

    private String error;

    private String logs;  // JSON

    @TableField("created_at")
    private LocalDateTime createdAt;
}
