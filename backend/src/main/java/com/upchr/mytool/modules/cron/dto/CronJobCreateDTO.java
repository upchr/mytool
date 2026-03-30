package com.upchr.mytool.modules.cron.dto;

import lombok.Data;

import java.util.List;

/**
 * 任务创建 DTO
 */
@Data
public class CronJobCreateDTO {

    private List<Long> nodeIds;  // 支持批量创建

    private Long nodeId;  // 单个创建

    private String name;

    private String schedule;

    private String command;

    private String description;

    private Boolean isNotice = false;

    private Integer errorTimes = 3;

    private Boolean isActive = true;
}
