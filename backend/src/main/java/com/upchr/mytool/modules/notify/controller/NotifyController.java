package com.upchr.mytool.modules.notify.controller;

import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.notify.service.NotifyService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 通知控制器
 */
@Tag(name = "通知管理")
@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
public class NotifyController {

    private final NotifyService notifyService;

    @GetMapping("/services")
    public BaseResponse<List<Map<String, Object>>> getServices() {
        return BaseResponse.success(notifyService.getServices());
    }

    @GetMapping("/services/{id}")
    public BaseResponse<Map<String, Object>> getService(@PathVariable Long id) {
        Map<String, Object> service = notifyService.getService(id);
        if (service == null) {
            throw new BusinessException("渠道不存在");
        }
        return BaseResponse.success(service);
    }

    @PutMapping("/services/{id}")
    public BaseResponse<Map<String, String>> updateService(@PathVariable Long id, @RequestBody Map<String, Object> data) {
        notifyService.updateService(id, data);
        Map<String, String> result = new java.util.HashMap<>();
        result.put("message", "配置更新成功");
        return BaseResponse.success(result);
    }

    @PutMapping("/services/status/{id}")
    public BaseResponse<Map<String, String>> updateServiceStatus(@PathVariable Long id, @RequestBody Map<String, Boolean> body) {
        Boolean isEnabled = body.get("is_enabled");
        notifyService.updateServiceStatus(id, isEnabled);
        Map<String, String> result = new java.util.HashMap<>();
        result.put("message", "配置状态成功");
        return BaseResponse.success(result);
    }

    @PostMapping("/test/{id}")
    public BaseResponse<Void> testService(@PathVariable Long id) {
        notifyService.testService(id);
        return BaseResponse.success();
    }
}
