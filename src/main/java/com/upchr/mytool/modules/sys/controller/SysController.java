package com.upchr.mytool.modules.sys.controller;

import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.sys.dto.LoginDTO;
import com.upchr.mytool.modules.sys.dto.ResetPasswordDTO;
import com.upchr.mytool.modules.sys.dto.SysInitDTO;
import com.upchr.mytool.modules.sys.service.SysService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 系统控制器
 */
@Tag(name = "系统管理")
@RestController
@RequestMapping("/sys")
@RequiredArgsConstructor
public class SysController {

    private final SysService sysService;

    @Operation(summary = "检查初始化状态")
    @GetMapping("/init/check")
    public BaseResponse<Map<String, Boolean>> checkInit() {
        Map<String, Boolean> data = new HashMap<>();
        data.put("is_initialized", sysService.isInitialized());
        return BaseResponse.success(data);
    }

    @Operation(summary = "初始化系统")
    @PostMapping("/init/setup")
    public BaseResponse<Map<String, String>> setup(@RequestBody @Validated SysInitDTO dto) {
        sysService.setup(dto.getPassword());
        Map<String, String> data = new HashMap<>();
        data.put("message", "初始化成功");
        return BaseResponse.success(data);
    }

    @Operation(summary = "登录")
    @PostMapping("/login")
    public BaseResponse<Map<String, String>> login(@RequestBody @Validated LoginDTO dto) {
        String token = sysService.login(dto.getPassword());
        Map<String, String> data = new HashMap<>();
        data.put("token", token);
        return BaseResponse.success(data);
    }

    @Operation(summary = "重置密码")
    @PostMapping("/resetPassword")
    public BaseResponse<Void> resetPassword(@RequestBody @Validated ResetPasswordDTO dto) {
        sysService.resetPassword(dto.getOldPassword(), dto.getPassword());
        return BaseResponse.success();
    }

    @Operation(summary = "获取运行时长")
    @GetMapping("/runtime")
    public BaseResponse<Map<String, Object>> getRuntime() {
        return BaseResponse.success(sysService.getRuntime());
    }
}
