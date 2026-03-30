package com.upchr.mytool.modules.notify.service;

import cn.hutool.http.HttpUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.modules.notify.entity.NotificationService;
import com.upchr.mytool.modules.notify.mapper.NotificationServiceMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 通知服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NotifyService extends ServiceImpl<NotificationServiceMapper, NotificationService> {

    /**
     * 获取所有服务
     */
    public List<Map<String, Object>> getServices() {
        List<NotificationService> services = list();
        
        if (services.isEmpty()) {
            // 初始化默认服务
            initDefaultServices();
            services = list();
        }

        return services.stream().map(this::toMap).toList();
    }

    /**
     * 获取单个服务
     */
    public Map<String, Object> getService(Long id) {
        NotificationService service = getById(id);
        if (service == null) {
            return null;
        }
        return toMap(service);
    }

    /**
     * 更新服务
     */
    public void updateService(Long id, Map<String, Object> data) {
        NotificationService service = getById(id);
        if (service == null) {
            throw new BusinessException("服务不存在");
        }

        service.setServiceName((String) data.get("service_name"));
        service.setIsEnabled((Boolean) data.get("is_enabled"));
        
        Object config = data.get("config");
        if (config != null) {
            service.setConfig(JSONUtil.toJsonStr(config));
        }

        service.setUpdatedAt(LocalDateTime.now());
        updateById(service);
    }

    /**
     * 更新服务状态
     */
    public void updateServiceStatus(Long id, Boolean isEnabled) {
        NotificationService service = getById(id);
        if (service == null) {
            throw new BusinessException("服务不存在");
        }

        service.setIsEnabled(isEnabled);
        service.setUpdatedAt(LocalDateTime.now());
        updateById(service);
    }

    /**
     * 测试服务
     */
    @Async("asyncExecutor")
    public void testService(Long id) {
        NotificationService service = getById(id);
        if (service == null) {
            log.error("服务不存在: {}", id);
            return;
        }

        try {
            sendNotification("测试通知", "这是一个测试通知，用于验证系统功能。", id);
            log.info("测试通知发送成功: {}", service.getServiceName());
        } catch (Exception e) {
            log.error("测试通知发送失败: {}", e.getMessage());
        }
    }

    /**
     * 发送通知
     */
    public Map<String, Object> sendNotification(String title, String content, Long serviceId) {
        NotificationService service = getById(serviceId);
        if (service == null || !Boolean.TRUE.equals(service.getIsEnabled())) {
            throw new BusinessException("服务不存在或未启用");
        }

        Map<String, Object> config = service.getConfig() != null ? 
                JSONUtil.toBean(service.getConfig(), Map.class) : new HashMap<>();

        return switch (service.getServiceType()) {
            case "wecom" -> sendWeCom(title, content, config);
            case "bark" -> sendBark(title, content, config);
            case "dingtalk" -> sendDingTalk(title, content, config);
            case "feishu" -> sendFeishu(title, content, config);
            case "email" -> sendEmail(title, content, config);
            default -> throw new BusinessException("不支持的服务类型: " + service.getServiceType());
        };
    }

    /**
     * 广播通知（发送到所有启用的服务）
     */
    @Async("asyncExecutor")
    public void sendBroadcast(String title, String content) {
        List<NotificationService> services = lambdaQuery()
                .eq(NotificationService::getIsEnabled, true)
                .list();

        for (NotificationService service : services) {
            try {
                sendNotification(title, content, service.getId());
                log.info("广播通知发送成功: {}", service.getServiceName());
            } catch (Exception e) {
                log.error("广播通知发送失败 [{}]: {}", service.getServiceName(), e.getMessage());
            }
        }
    }

    // ========== 发送方法 ==========

    private Map<String, Object> sendWeCom(String title, String content, Map<String, Object> config) {
        String webhook = (String) config.get("webhook");
        if (webhook == null) {
            throw new BusinessException("企业微信 webhook 未配置");
        }

        Map<String, Object> body = new HashMap<>();
        body.put("msgtype", "text");
        Map<String, String> text = new HashMap<>();
        text.put("content", title + "\n" + content);
        body.put("text", text);

        String result = HttpUtil.post(webhook, JSONUtil.toJsonStr(body));
        log.info("企业微信发送结果: {}", result);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("result", result);
        return response;
    }

    private Map<String, Object> sendBark(String title, String content, Map<String, Object> config) {
        String url = (String) config.get("url");
        if (url == null) {
            throw new BusinessException("Bark URL 未配置");
        }

        String fullUrl = url + "/" + title + "/" + content;
        String result = HttpUtil.get(fullUrl);
        log.info("Bark 发送结果: {}", result);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("result", result);
        return response;
    }

    private Map<String, Object> sendDingTalk(String title, String content, Map<String, Object> config) {
        String webhook = (String) config.get("webhook");
        if (webhook == null) {
            throw new BusinessException("钉钉 webhook 未配置");
        }

        Map<String, Object> body = new HashMap<>();
        body.put("msgtype", "text");
        Map<String, String> text = new HashMap<>();
        text.put("content", title + "\n" + content);
        body.put("text", text);

        String result = HttpUtil.post(webhook, JSONUtil.toJsonStr(body));
        log.info("钉钉发送结果: {}", result);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("result", result);
        return response;
    }

    private Map<String, Object> sendFeishu(String title, String content, Map<String, Object> config) {
        String webhook = (String) config.get("webhook");
        if (webhook == null) {
            throw new BusinessException("飞书 webhook 未配置");
        }

        Map<String, Object> body = new HashMap<>();
        body.put("msg_type", "text");
        Map<String, String> text = new HashMap<>();
        text.put("text", title + "\n" + content);
        body.put("content", text);

        String result = HttpUtil.post(webhook, JSONUtil.toJsonStr(body));
        log.info("飞书发送结果: {}", result);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("result", result);
        return response;
    }

    private Map<String, Object> sendEmail(String title, String content, Map<String, Object> config) {
        // TODO: 实现邮件发送
        log.info("邮件发送: {} - {}", title, content);
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "邮件发送功能待实现");
        return response;
    }

    // ========== 辅助方法 ==========

    private void initDefaultServices() {
        String[][] defaults = {
                {"wecom", "企业微信"},
                {"bark", "Bark"},
                {"dingtalk", "钉钉"},
                {"feishu", "飞书"},
                {"email", "邮件"}
        };

        for (String[] item : defaults) {
            NotificationService service = new NotificationService();
            service.setServiceType(item[0]);
            service.setServiceName(item[1]);
            service.setIsEnabled(false);
            service.setCreatedAt(LocalDateTime.now());
            service.setUpdatedAt(LocalDateTime.now());
            save(service);
        }

        log.info("默认通知服务初始化完成");
    }

    private Map<String, Object> toMap(NotificationService service) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", service.getId());
        map.put("service_type", service.getServiceType());
        map.put("service_name", service.getServiceName());
        map.put("is_enabled", service.getIsEnabled());
        map.put("config", service.getConfig() != null ? JSONUtil.parseObj(service.getConfig()) : new HashMap<>());
        map.put("created_at", service.getCreatedAt());
        map.put("updated_at", service.getUpdatedAt());
        return map;
    }
}
