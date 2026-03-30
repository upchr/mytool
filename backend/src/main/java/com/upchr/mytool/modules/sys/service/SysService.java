package com.upchr.mytool.modules.sys.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.utils.JwtUtil;
import com.upchr.mytool.common.utils.SecurityUtil;
import com.upchr.mytool.modules.sys.entity.SystemConfig;
import com.upchr.mytool.modules.sys.mapper.SystemConfigMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 系统服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysService {

    private final SystemConfigMapper systemConfigMapper;
    private final SecurityUtil securityUtil;
    private final JwtUtil jwtUtil;

    /**
     * 检查是否已初始化
     */
    public boolean isInitialized() {
        SystemConfig config = systemConfigMapper.selectById(1);
        return config != null && Boolean.TRUE.equals(config.getIsInitialized());
    }

    /**
     * 初始化系统
     */
    public void setup(String password) {
        if (isInitialized()) {
            throw new BusinessException("系统已初始化");
        }

        String passwordHash = securityUtil.hashPassword(password);

        SystemConfig config = new SystemConfig();
        config.setId(1L);
        config.setIsInitialized(true);
        config.setAdminPasswordHash(passwordHash);
        config.setAppStartTime(LocalDateTime.now());

        systemConfigMapper.insert(config);
        log.info("系统初始化完成");
    }

    /**
     * 登录
     */
    public String login(String password) {
        SystemConfig config = systemConfigMapper.selectById(1);
        if (config == null || !Boolean.TRUE.equals(config.getIsInitialized())) {
            throw new BusinessException("系统未初始化");
        }

        if (!securityUtil.verifyPassword(password, config.getAdminPasswordHash())) {
            throw new BusinessException("密码错误");
        }

        // 更新启动时间
        config.setAppStartTime(LocalDateTime.now());
        systemConfigMapper.updateById(config);

        // 生成 Token
        Map<String, Object> claims = new HashMap<>();
        claims.put("user_id", 1L);
        claims.put("username", "admin");
        claims.put("role", "admin");

        return jwtUtil.generateToken(claims);
    }

    /**
     * 重置密码
     */
    public void resetPassword(String oldPassword, String newPassword) {
        SystemConfig config = systemConfigMapper.selectById(1);
        if (config == null || !Boolean.TRUE.equals(config.getIsInitialized())) {
            throw new BusinessException("系统未初始化");
        }

        if (!securityUtil.verifyPassword(oldPassword, config.getAdminPasswordHash())) {
            throw new BusinessException("密码错误");
        }

        config.setAdminPasswordHash(securityUtil.hashPassword(newPassword));
        systemConfigMapper.updateById(config);
    }

    /**
     * 获取运行时长
     */
    public Map<String, Object> getRuntime() {
        SystemConfig config = systemConfigMapper.selectById(1);
        LocalDateTime startTime = config != null ? config.getAppStartTime() : null;
        LocalDateTime currentTime = LocalDateTime.now();

        Map<String, Object> result = new HashMap<>();
        result.put("start_time", startTime != null ? startTime.toString() : null);
        result.put("current_time", currentTime.toString());

        if (startTime != null) {
            long seconds = Duration.between(startTime, currentTime).getSeconds();
            result.put("runtime_seconds", seconds);

            long days = seconds / 86400;
            long hours = (seconds % 86400) / 3600;
            long minutes = (seconds % 3600) / 60;
            long secs = seconds % 60;

            StringBuilder sb = new StringBuilder();
            if (days > 0) sb.append(days).append("天");
            if (hours > 0) sb.append(hours).append("小时");
            if (minutes > 0) sb.append(minutes).append("分钟");
            if (secs > 0 || sb.length() == 0) sb.append(secs).append("秒");
            result.put("runtime_str", sb.toString());
        } else {
            result.put("runtime_seconds", 0);
            result.put("runtime_str", "未启动");
        }

        return result;
    }
}
