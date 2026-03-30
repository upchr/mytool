package com.upchr.mytool.modules.node.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.upchr.mytool.common.exception.BusinessException;
import com.upchr.mytool.core.ssh.SSHClient;
import com.upchr.mytool.modules.node.dto.NodeCreateDTO;
import com.upchr.mytool.modules.node.entity.CredentialTemplate;
import com.upchr.mytool.modules.node.entity.Node;
import com.upchr.mytool.modules.node.mapper.CredentialTemplateMapper;
import com.upchr.mytool.modules.node.mapper.NodeMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 节点服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NodeService extends ServiceImpl<NodeMapper, Node> {

    private final CredentialTemplateMapper credentialTemplateMapper;

    public Node createNode(NodeCreateDTO dto) {
        // 检查名称是否重复
        if (lambdaQuery().eq(Node::getName, dto.getName()).exists()) {
            throw new BusinessException("节点名称已存在");
        }

        Node node = new Node();
        node.setName(dto.getName());
        node.setHost(dto.getHost());
        node.setPort(dto.getPort());
        node.setUsername(dto.getUsername());
        node.setAuthType(dto.getAuthType());
        node.setPassword(dto.getPassword());
        node.setPrivateKey(dto.getPrivateKey());
        node.setIsActive(dto.getIsActive());

        save(node);
        return node;
    }

    public List<Node> getNodes(boolean activeOnly) {
        LambdaQueryWrapper<Node> wrapper = new LambdaQueryWrapper<>();
        if (activeOnly) {
            wrapper.eq(Node::getIsActive, true);
        }
        wrapper.orderByAsc(Node::getName);
        return list(wrapper);
    }

    public Node getNode(Long id) {
        return getById(id);
    }

    public Node updateNode(Long id, NodeCreateDTO dto) {
        Node node = getById(id);
        if (node == null) {
            return null;
        }

        // 检查名称是否重复（排除自己）
        if (!node.getName().equals(dto.getName()) && 
            lambdaQuery().eq(Node::getName, dto.getName()).exists()) {
            throw new BusinessException("节点名称已存在");
        }

        node.setName(dto.getName());
        node.setHost(dto.getHost());
        node.setPort(dto.getPort());
        node.setUsername(dto.getUsername());
        node.setAuthType(dto.getAuthType());
        node.setPassword(dto.getPassword());
        node.setPrivateKey(dto.getPrivateKey());

        updateById(node);
        return node;
    }

    public boolean deleteNode(Long id) {
        return removeById(id);
    }

    public int batchDeleteNodes(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return 0;
        }
        return (int) removeByIds(ids);
    }

    public boolean toggleNodeStatus(Long id, boolean isActive) {
        Node node = getById(id);
        if (node == null) {
            return false;
        }
        node.setIsActive(isActive);
        updateById(node);
        return true;
    }

    public void testConnection(Long id) {
        Node node = getById(id);
        if (node == null) {
            throw new BusinessException("节点不存在");
        }

        SSHClient ssh = new SSHClient(
                node.getHost(),
                node.getPort(),
                node.getUsername(),
                node.getPassword(),
                node.getPrivateKey()
        );

        try {
            ssh.connect();
            ssh.close();
        } catch (Exception e) {
            throw new BusinessException("连接失败: " + e.getMessage());
        }
    }

    // ========== 凭据模板 ==========

    public List<CredentialTemplate> getCredentialTemplates() {
        return credentialTemplateMapper.selectList(
                new LambdaQueryWrapper<CredentialTemplate>()
                        .orderByAsc(CredentialTemplate::getName)
        );
    }

    public CredentialTemplate createCredentialTemplate(CredentialTemplate template) {
        if (credentialTemplateMapper.selectCount(
                new LambdaQueryWrapper<CredentialTemplate>()
                        .eq(CredentialTemplate::getName, template.getName())
        ) > 0) {
            throw new BusinessException("模板名称已存在");
        }
        credentialTemplateMapper.insert(template);
        return template;
    }

    public CredentialTemplate updateCredentialTemplate(Long id, CredentialTemplate template) {
        CredentialTemplate existing = credentialTemplateMapper.selectById(id);
        if (existing == null) {
            return null;
        }
        template.setId(id);
        credentialTemplateMapper.updateById(template);
        return template;
    }

    public boolean deleteCredentialTemplate(Long id) {
        return credentialTemplateMapper.deleteById(id) > 0;
    }
}
