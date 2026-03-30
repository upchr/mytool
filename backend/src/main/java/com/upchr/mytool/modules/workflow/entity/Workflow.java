package com.upchr.mytool.modules.workflow.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 工作流实体
 */
@Data
@TableName("workflows")
public class Workflow {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("workflow_id")
    private String workflowId;

    private String name;

    private String description;

    private String schedule;

    private String nodes;  // JSON

    private String edges;  // JSON

    @TableField("is_active")
    private Boolean isActive;

    @TableField("default_version")
    private Integer defaultVersion;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
