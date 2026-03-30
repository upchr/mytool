package com.upchr.mytool.modules.node.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 节点实体
 */
@Data
@TableName("nodes")
public class Node {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String host;

    private Integer port;

    private String username;

    @TableField("auth_type")
    private String authType;

    private String password;

    @TableField("private_key")
    private String privateKey;

    @TableField("is_active")
    private Boolean isActive;
}
