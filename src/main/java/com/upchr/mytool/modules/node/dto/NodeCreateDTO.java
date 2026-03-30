package com.upchr.mytool.modules.node.dto;

import lombok.Data;

/**
 * 节点创建 DTO
 */
@Data
public class NodeCreateDTO {

    private String name;

    private String host;

    private Integer port = 22;

    private String username;

    private String authType = "password";

    private String password;

    private String privateKey;

    private Boolean isActive = true;
}
