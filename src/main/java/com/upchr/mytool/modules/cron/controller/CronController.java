package com.upchr.mytool.modules.cron.controller;

import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.cron.dto.CronJobCreateDTO;
import com.upchr.mytool.modules.cron.dto.CronReq;
import com.upchr.mytool.modules.cron.dto.ManualExecutionRequest;
import com.upchr.mytool.modules.cron.entity.JobExecution;
import com.upchr.mytool.modules.cron.service.CronService;
import com.upchr.mytool.modules.node.dto.NodeRequest;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 定时任务控制器
 */
@Tag(name = "定时任务")
@RestController
@RequestMapping("/cron")
@RequiredArgsConstructor
public class CronController {

    private final CronService cronService;

    @PostMapping("/jobs")
    public BaseResponse<List<Map<String, Object>>> createJobs(@RequestBody CronJobCreateDTO dto) {
        return BaseResponse.success(cronService.createJobs(dto));
    }

    @PostMapping("/jobsList")
    public BaseResponse<List<Map<String, Object>>> listJobs(@RequestBody NodeRequest request) {
        return BaseResponse.success(cronService.getJobs(request.getNodeIds()));
    }

    @PutMapping("/jobs/{id}")
    public BaseResponse<Map<String, Object>> updateJob(@PathVariable Long id, @RequestBody Map<String, Object> data) {
        if (!cronService.updateJob(id, data)) {
            throw new BusinessException("任务不存在");
        }
        return BaseResponse.success(cronService.getJob(id));
    }

    @DeleteMapping("/jobs/{id}")
    public BaseResponse<Map<String, Object>> deleteJob(@PathVariable Long id) {
        boolean success = cronService.removeJob(id);
        if (!success) {
            throw new BusinessException("任务不存在");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("status", "ok");
        data.put("id", id);
        return BaseResponse.success(data);
    }

    @PatchMapping("/jobs/{id}/toggle")
    public BaseResponse<Map<String, Object>> toggleJob(@PathVariable Long id, @RequestBody Map<String, Boolean> body) {
        boolean isActive = body.getOrDefault("is_active", true);
        boolean success = cronService.toggleJob(id, isActive);
        if (!success) {
            throw new BusinessException("任务不存在");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("status", "ok");
        data.put("is_active", isActive);
        return BaseResponse.success(data);
    }

    @PostMapping("/jobs/execute")
    public BaseResponse<List<Map<String, Object>>> executeJobs(@RequestBody ManualExecutionRequest request) {
        if ((request.getJobIds() == null || request.getJobIds().isEmpty()) &&
            (request.getNodeIds() == null || request.getNodeIds().isEmpty())) {
            throw new BusinessException("必须指定任务ID或节点ID");
        }
        return BaseResponse.success(cronService.executeJobs(request));
    }

    @GetMapping("/jobs/{id}/executions")
    public BaseResponse<List<JobExecution>> getExecutions(@PathVariable Long id, @RequestParam(defaultValue = "10") int limit) {
        return BaseResponse.success(cronService.getExecutions(id, limit));
    }

    @GetMapping("/executions/{id}")
    public BaseResponse<JobExecution> getExecution(@PathVariable Long id) {
        JobExecution execution = cronService.getExecution(id);
        if (execution == null) {
            throw new BusinessException("执行记录不存在");
        }
        return BaseResponse.success(execution);
    }

    @PostMapping("/executions/{id}/stop")
    public BaseResponse<Map<String, String>> stopExecution(@PathVariable Long id) {
        cronService.stopExecution(id);
        Map<String, String> data = new HashMap<>();
        data.put("status", "ok");
        data.put("message", "中断请求已发送");
        return BaseResponse.success(data);
    }

    @PostMapping("/jobs/crons")
    public BaseResponse<List<Map<String, String>>> getNextCrons(@RequestBody CronReq req) {
        return BaseResponse.success(cronService.getNextCrons(req));
    }

    @PostMapping("/jobs/sync")
    public BaseResponse<Map<String, Object>> syncJobs() {
        // TODO: 实现同步到调度器
        Map<String, Object> data = new HashMap<>();
        data.put("message", "已同步 0 个任务");
        return BaseResponse.success(data);
    }
}
