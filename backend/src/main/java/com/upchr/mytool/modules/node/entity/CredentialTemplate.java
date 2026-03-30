package com.upchr.mytool.modules.node.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 凭据模板实体
 */
@Data
@TableName("credential_templates")
public class CredentialTemplate {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String username;

    @TableField("auth_type")
    private String authType;

    private String password;

    @TableField("private_key")
    private String privateKey;

    @TableField("is_active")
    private Boolean isActive;
}
