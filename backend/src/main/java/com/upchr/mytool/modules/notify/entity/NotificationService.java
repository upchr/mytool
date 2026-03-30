package com.upchr.mytool.modules.notify.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 通知服务实体
 */
@Data
@TableName("notification_services")
public class NotificationService {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("service_type")
    private String serviceType;

    @TableField("service_name")
    private String serviceName;

    @TableField("is_enabled")
    private Boolean isEnabled;

    private String config;  // JSON

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
