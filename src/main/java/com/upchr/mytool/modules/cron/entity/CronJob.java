package com.upchr.mytool.modules.cron.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 定时任务实体
 */
@Data
@TableName("cron_jobs")
public class CronJob {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("node_id")
    private Long nodeId;

    private String name;

    private String schedule;

    private String command;

    private String description;

    @TableField("is_notice")
    private Boolean isNotice;

    @TableField("error_times")
    private Integer errorTimes;

    @TableField("consecutive_failures")
    private Integer consecutiveFailures;

    @TableField("is_active")
    private Boolean isActive;
}
