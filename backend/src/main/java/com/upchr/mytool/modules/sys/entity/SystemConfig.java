package com.upchr.mytool.modules.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 系统配置实体
 */
@Data
@TableName("system_config")
public class SystemConfig {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("is_initialized")
    private Boolean isInitialized;

    @TableField("admin_password_hash")
    private String adminPasswordHash;

    @TableField("app_start_time")
    private LocalDateTime appStartTime;
}
