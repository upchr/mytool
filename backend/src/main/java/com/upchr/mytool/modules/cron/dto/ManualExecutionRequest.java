package com.upchr.mytool.modules.cron.dto;

import lombok.Data;

import java.util.List;

/**
 * 手动执行请求
 */
@Data
public class ManualExecutionRequest {

    private List<Long> jobIds;

    private List<Long> nodeIds;
}
