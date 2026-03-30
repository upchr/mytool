package com.upchr.mytool.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.lang.reflect.Method;
import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 统一线程池配置
 * 
 * 所有异步任务统一使用此线程池，便于：
 * 1. 统一监控和管理
 * 2. 线程命名便于追溯
 * 3. 拒绝策略统一处理
 */
@Slf4j
@Configuration
public class ThreadPoolConfig implements AsyncConfigurer {

    @Value("${thread-pool.core-size:4}")
    private int coreSize;

    @Value("${thread-pool.max-size:16}")
    private int maxSize;

    @Value("${thread-pool.queue-capacity:100}")
    private int queueCapacity;

    @Value("${thread-pool.keep-alive-seconds:60}")
    private int keepAliveSeconds;

    @Value("${thread-pool.thread-name-prefix:mytool-async-}")
    private String threadNamePrefix;

    /**
     * 主异步任务线程池
     */
    @Bean("asyncExecutor")
    public ThreadPoolTaskExecutor asyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(coreSize);
        executor.setMaxPoolSize(maxSize);
        executor.setQueueCapacity(queueCapacity);
        executor.setKeepAliveSeconds(keepAliveSeconds);
        executor.setThreadNamePrefix(threadNamePrefix);
        
        // 拒绝策略：调用者运行
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        
        // 等待所有任务完成后再关闭线程池
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        
        executor.initialize();
        log.info("✅ 异步线程池初始化完成: core={}, max={}, queue={}, prefix={}", 
                coreSize, maxSize, queueCapacity, threadNamePrefix);
        
        return executor;
    }

    /**
     * Workflow 专用线程池（独立，避免与其他任务竞争）
     */
    @Bean("workflowExecutor")
    public ThreadPoolTaskExecutor workflowExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(50);
        executor.setKeepAliveSeconds(120);
        executor.setThreadNamePrefix("mytool-workflow-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(120);
        executor.initialize();
        
        log.info("✅ Workflow 线程池初始化完成");
        return executor;
    }

    /**
     * Spring @Async 默认使用的线程池
     */
    @Override
    public Executor getAsyncExecutor() {
        return asyncExecutor();
    }
}
