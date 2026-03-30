package com.upchr.mytool.modules.cron.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.cronutils.model.Cron;
import com.cronutils.model.CronType;
import com.cronutils.model.definition.CronDefinitionBuilder;
import com.cronutils.model.time.ExecutionTime;
import com.cronutils.parser.CronParser;
import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.core.ssh.SSHClient;
import com.upchr.mytool.modules.cron.dto.CronJobCreateDTO;
import com.upchr.mytool.modules.cron.dto.CronReq;
import com.upchr.mytool.modules.cron.dto.ManualExecutionRequest;
import com.upchr.mytool.modules.cron.entity.CronJob;
import com.upchr.mytool.modules.cron.entity.JobExecution;
import com.upchr.mytool.modules.cron.mapper.CronJobMapper;
import com.upchr.mytool.modules.cron.mapper.JobExecutionMapper;
import com.upchr.mytool.modules.node.entity.Node;
import com.upchr.mytool.modules.node.mapper.NodeMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 定时任务服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CronService extends ServiceImpl<CronJobMapper, CronJob> {

    private final JobExecutionMapper executionMapper;
    private final NodeMapper nodeMapper;

    // 执行中的任务（用于中断）
    private final Map<Long, Boolean> runningTasks = new ConcurrentHashMap<>();

    /**
     * 创建任务
     */
    public List<Map<String, Object>> createJobs(CronJobCreateDTO dto) {
        List<Map<String, Object>> results = new ArrayList<>();

        List<Long> nodeIds = dto.getNodeIds() != null ? dto.getNodeIds() : 
                (dto.getNodeId() != null ? List.of(dto.getNodeId()) : Collections.emptyList());

        for (Long nodeId : nodeIds) {
            CronJob job = new CronJob();
            job.setNodeId(nodeId);
            job.setName(dto.getName());
            job.setSchedule(dto.getSchedule());
            job.setCommand(dto.getCommand());
            job.setDescription(dto.getDescription());
            job.setIsNotice(dto.getIsNotice());
            job.setErrorTimes(dto.getErrorTimes());
            job.setConsecutiveFailures(0);
            job.setIsActive(dto.getIsActive());

            save(job);

            Map<String, Object> result = new HashMap<>();
            result.put("id", job.getId());
            result.put("node_id", nodeId);
            result.put("name", job.getName());
            results.add(result);
        }

        return results;
    }

    /**
     * 获取任务列表
     */
    public List<Map<String, Object>> getJobs(List<Long> nodeIds) {
        LambdaQueryWrapper<CronJob> wrapper = new LambdaQueryWrapper<>();
        
        if (nodeIds != null && !nodeIds.isEmpty()) {
            wrapper.in(CronJob::getNodeId, nodeIds);
        }

        wrapper.orderByAsc(CronJob::getName);

        List<CronJob> jobs = list(wrapper);
        List<Map<String, Object>> results = new ArrayList<>();

        for (CronJob job : jobs) {
            Map<String, Object> jobMap = new HashMap<>();
            jobMap.put("id", job.getId());
            jobMap.put("node_id", job.getNodeId());
            jobMap.put("name", job.getName());
            jobMap.put("schedule", job.getSchedule());
            jobMap.put("command", job.getCommand());
            jobMap.put("description", job.getDescription());
            jobMap.put("is_notice", job.getIsNotice());
            jobMap.put("error_times", job.getErrorTimes());
            jobMap.put("consecutive_failures", job.getConsecutiveFailures());
            jobMap.put("is_active", job.getIsActive());

            // 计算下次执行时间
            if (Boolean.TRUE.equals(job.getIsActive())) {
                try {
                    String nextRun = calculateNextRun(job.getSchedule());
                    jobMap.put("next_run", nextRun);
                } catch (Exception e) {
                    jobMap.put("next_run", null);
                }
            } else {
                jobMap.put("next_run", null);
            }

            results.add(jobMap);
        }

        return results;
    }

    /**
     * 获取单个任务
     */
    public Map<String, Object> getJob(Long id) {
        CronJob job = getById(id);
        if (job == null) {
            return null;
        }
        Map<String, Object> map = new HashMap<>();
        map.put("id", job.getId());
        map.put("node_id", job.getNodeId());
        map.put("name", job.getName());
        map.put("schedule", job.getSchedule());
        map.put("command", job.getCommand());
        map.put("description", job.getDescription());
        map.put("is_active", job.getIsActive());
        return map;
    }

    /**
     * 更新任务
     */
    public boolean updateJob(Long id, Map<String, Object> data) {
        CronJob job = getById(id);
        if (job == null) {
            return false;
        }

        if (data.containsKey("name")) job.setName((String) data.get("name"));
        if (data.containsKey("schedule")) job.setSchedule((String) data.get("schedule"));
        if (data.containsKey("command")) job.setCommand((String) data.get("command"));
        if (data.containsKey("description")) job.setDescription((String) data.get("description"));
        if (data.containsKey("is_active")) job.setIsActive((Boolean) data.get("is_active"));

        updateById(job);
        return true;
    }

    /**
     * 删除任务
     */
    public boolean removeJob(Long id) {
        return removeById(id);
    }

    /**
     * 切换任务状态
     */
    public boolean toggleJob(Long id, boolean isActive) {
        CronJob job = getById(id);
        if (job == null) {
            return false;
        }
        job.setIsActive(isActive);
        updateById(job);
        return true;
    }

    /**
     * 执行任务
     */
    @Async("asyncExecutor")
    public void executeJob(Long jobId, String triggeredBy) {
        CronJob job = getById(jobId);
        if (job == null) {
            log.error("任务不存在: {}", jobId);
            return;
        }

        Node node = nodeMapper.selectById(job.getNodeId());
        if (node == null) {
            log.error("节点不存在: {}", job.getNodeId());
            return;
        }

        // 创建执行记录
        JobExecution execution = new JobExecution();
        execution.setJobId(jobId);
        execution.setStartTime(LocalDateTime.now());
        execution.setStatus("running");
        execution.setTriggeredBy(triggeredBy);
        executionMapper.insert(execution);

        runningTasks.put(execution.getId(), true);

        SSHClient ssh = null;
        try {
            ssh = new SSHClient(
                    node.getHost(),
                    node.getPort(),
                    node.getUsername(),
                    node.getPassword(),
                    node.getPrivateKey()
            );
            ssh.connect();

            SSHClient.SSHResult result = ssh.executeCommand(job.getCommand(), 60);

            execution.setStatus(result.isSuccess() ? "success" : "failed");
            execution.setOutput(result.getOutput());
            execution.setError(result.getError());
            execution.setEndTime(LocalDateTime.now());

            // 更新连续失败次数
            if (result.isSuccess()) {
                job.setConsecutiveFailures(0);
            } else {
                int failures = (job.getConsecutiveFailures() != null ? job.getConsecutiveFailures() : 0) + 1;
                job.setConsecutiveFailures(failures);
            }
            updateById(job);

        } catch (Exception e) {
            execution.setStatus("failed");
            execution.setError(e.getMessage());
            execution.setEndTime(LocalDateTime.now());
            log.error("任务执行失败: {}", e.getMessage());
        } finally {
            if (ssh != null) {
                ssh.close();
            }
            executionMapper.updateById(execution);
            runningTasks.remove(execution.getId());
        }
    }

    /**
     * 批量执行任务
     */
    public List<Map<String, Object>> executeJobs(ManualExecutionRequest request) {
        List<Map<String, Object>> results = new ArrayList<>();

        if (request.getJobIds() != null) {
            for (Long jobId : request.getJobIds()) {
                executeJob(jobId, "manual");
                Map<String, Object> result = new HashMap<>();
                result.put("job_id", jobId);
                result.put("status", "started");
                results.add(result);
            }
        }

        return results;
    }

    /**
     * 获取执行记录
     */
    public List<JobExecution> getExecutions(Long jobId, int limit) {
        return executionMapper.selectList(
                new LambdaQueryWrapper<JobExecution>()
                        .eq(JobExecution::getJobId, jobId)
                        .orderByDesc(JobExecution::getStartTime)
                        .last("LIMIT " + limit)
        );
    }

    /**
     * 获取单个执行记录
     */
    public JobExecution getExecution(Long executionId) {
        return executionMapper.selectById(executionId);
    }

    /**
     * 停止执行
     */
    public void stopExecution(Long executionId) {
        runningTasks.put(executionId, false);
    }

    /**
     * 计算下次执行时间
     */
    public String calculateNextRun(String schedule) {
        try {
            CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.UNIX));
            Cron cron = parser.parse(schedule);
            ExecutionTime executionTime = ExecutionTime.forCron(cron);
            Optional<ZonedDateTime> next = executionTime.nextExecution(ZonedDateTime.now());
            return next.map(z -> z.withZoneSameInstant(ZoneId.of("Asia/Shanghai")).toString()).orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 获取未来 5 次执行时间
     */
    public List<Map<String, String>> getNextCrons(CronReq req) {
        List<Map<String, String>> results = new ArrayList<>();
        try {
            CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.UNIX));
            Cron cron = parser.parse(req.getCron());
            ExecutionTime executionTime = ExecutionTime.forCron(cron);
            
            ZonedDateTime now = ZonedDateTime.now();
            for (int i = 0; i < 5; i++) {
                Optional<ZonedDateTime> next = executionTime.nextExecution(now);
                if (next.isPresent()) {
                    now = next.get();
                    Map<String, String> item = new HashMap<>();
                    item.put("next_run", now.withZoneSameInstant(ZoneId.of("Asia/Shanghai")).toString());
                    results.add(item);
                }
            }
        } catch (Exception e) {
            log.error("解析 cron 表达式失败: {}", e.getMessage());
        }
        return results;
    }
}
