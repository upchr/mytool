package com.upchr.mytool.modules.node.controller;

import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.common.result.BaseResponse;
import com.upchr.mytool.modules.node.dto.NodeCreateDTO;
import com.upchr.mytool.modules.node.dto.NodeRequest;
import com.upchr.mytool.modules.node.entity.CredentialTemplate;
import com.upchr.mytool.modules.node.entity.Node;
import com.upchr.mytool.modules.node.service.NodeService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 节点控制器
 */
@Tag(name = "节点管理")
@RestController
@RequestMapping("/nodes")
@RequiredArgsConstructor
public class NodeController {

    private final NodeService nodeService;

    @PostMapping
    public BaseResponse<Node> create(@RequestBody NodeCreateDTO dto) {
        return BaseResponse.success(nodeService.createNode(dto));
    }

    @GetMapping("/only_active/{activeOnly}")
    public BaseResponse<List<Node>> list(@PathVariable boolean activeOnly) {
        return BaseResponse.success(nodeService.getNodes(activeOnly));
    }

    @GetMapping("/{id}")
    public BaseResponse<Node> getById(@PathVariable Long id) {
        Node node = nodeService.getNode(id);
        if (node == null) {
            throw new BusinessException("节点不存在");
        }
        return BaseResponse.success(node);
    }

    @PutMapping("/{id}")
    public BaseResponse<Node> update(@PathVariable Long id, @RequestBody NodeCreateDTO dto) {
        Node node = nodeService.updateNode(id, dto);
        if (node == null) {
            throw new BusinessException("节点不存在");
        }
        return BaseResponse.success(node);
    }

    @DeleteMapping("/{id}")
    public BaseResponse<Map<String, Object>> delete(@PathVariable Long id) {
        boolean success = nodeService.deleteNode(id);
        if (!success) {
            throw new BusinessException("节点不存在");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("status", "ok");
        data.put("id", id);
        return BaseResponse.success(data);
    }

    @PatchMapping("/{id}/toggle")
    public BaseResponse<Map<String, Object>> toggle(@PathVariable Long id, @RequestBody Map<String, Boolean> body) {
        boolean isActive = body.getOrDefault("is_active", true);
        boolean success = nodeService.toggleNodeStatus(id, isActive);
        if (!success) {
            throw new BusinessException("节点不存在");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("status", "ok");
        data.put("is_active", isActive);
        return BaseResponse.success(data);
    }

    @PostMapping("/deleteBatch")
    public BaseResponse<Map<String, Object>> batchDelete(@RequestBody NodeRequest request) {
        if (request.getNodeIds() == null || request.getNodeIds().isEmpty()) {
            throw new BusinessException("节点ID列表不能为空");
        }
        int count = nodeService.batchDeleteNodes(request.getNodeIds());
        Map<String, Object> data = new HashMap<>();
        data.put("success", true);
        data.put("deleted_count", count);
        return BaseResponse.success(data);
    }

    @PostMapping("/{id}/test")
    public BaseResponse<Void> testConnection(@PathVariable Long id) {
        nodeService.testConnection(id);
        return BaseResponse.success();
    }

    // ========== 凭据模板 ==========

    @GetMapping("/credentials/")
    public BaseResponse<List<CredentialTemplate>> listCredentials() {
        return BaseResponse.success(nodeService.getCredentialTemplates());
    }

    @PostMapping("/credentials/")
    public BaseResponse<CredentialTemplate> createCredential(@RequestBody CredentialTemplate template) {
        return BaseResponse.success(nodeService.createCredentialTemplate(template));
    }

    @PutMapping("/credentials/{id}")
    public BaseResponse<CredentialTemplate> updateCredential(@PathVariable Long id, @RequestBody CredentialTemplate template) {
        CredentialTemplate updated = nodeService.updateCredentialTemplate(id, template);
        if (updated == null) {
            throw new BusinessException("模板不存在");
        }
        return BaseResponse.success(updated);
    }

    @DeleteMapping("/credentials/{id}")
    public BaseResponse<Void> deleteCredential(@PathVariable Long id) {
        boolean success = nodeService.deleteCredentialTemplate(id);
        if (!success) {
            throw new BusinessException("模板不存在");
        }
        return BaseResponse.success();
    }
}
