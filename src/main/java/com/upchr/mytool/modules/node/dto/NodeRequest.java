package com.upchr.mytool.modules.node.dto;

import lombok.Data;

import java.util.List;

/**
 * 节点请求 DTO
 */
@Data
public class NodeRequest {
    private List<Long> nodeIds;
}
