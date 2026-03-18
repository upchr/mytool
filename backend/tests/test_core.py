"""
ToolsPlus 单元测试
运行: pytest tests/
"""
import pytest
import asyncio
from datetime import datetime


# ========== 测试 Workflow 变量解析器 ==========

class TestWorkflowVariableResolver:
    """测试工作流变量解析器"""
    
    def test_resolve_simple_variable(self):
        """测试简单变量解析"""
        from app.modules.workflow.engine import WorkflowVariableResolver
        
        state = {
            "inputs": {"name": "test", "count": 5},
            "outputs": {}
        }
        
        result = WorkflowVariableResolver.resolve("Hello {{inputs.name}}", state)
        assert result == "Hello test"
    
    def test_resolve_output_variable(self):
        """测试输出变量解析"""
        from app.modules.workflow.engine import WorkflowVariableResolver
        
        state = {
            "inputs": {},
            "outputs": {
                "node1": {"result": "success", "data": 100}
            }
        }
        
        result = WorkflowVariableResolver.resolve("Result: {{outputs.node1.data}}", state)
        assert result == "Result: 100"
    
    def test_evaluate_condition(self):
        """测试条件表达式评估"""
        from app.modules.workflow.engine import WorkflowVariableResolver
        
        state = {
            "inputs": {"count": 10},
            "outputs": {}
        }
        
        result = WorkflowVariableResolver.evaluate_condition("{{inputs.count}} > 5", state)
        assert result is True
        
        result = WorkflowVariableResolver.evaluate_condition("{{inputs.count}} < 5", state)
        assert result is False


# ========== 测试 Plugin 权限系统 ==========

class TestPluginPermission:
    """测试插件权限系统"""
    
    def test_permission_decorator(self):
        """测试权限装饰器"""
        from app.modules.plugin.plugin_base import BasePlugin, require_permission, PluginPermission
        
        class TestPlugin(BasePlugin):
            plugin_id = "test-plugin"
            name = "Test Plugin"
            required_permissions = [PluginPermission.NETWORK]
            
            def get_config_schema(self):
                return {}
            
            @require_permission(PluginPermission.NETWORK)
            def do_network_request(self):
                return "success"
            
            @require_permission(PluginPermission.FILESYSTEM_WRITE)
            def write_file(self):
                return "success"
        
        # 测试有授权的情况
        plugin = TestPlugin({}, granted_permissions={PluginPermission.NETWORK})
        assert plugin.do_network_request() == "success"
        
        # 测试没有授权的情况
        with pytest.raises(PermissionError):
            plugin.write_file()


# ========== 测试 TaskTemplate 变量替换 ==========

class TestTaskTemplate:
    """测试任务模板"""
    
    def test_variable_replacement(self):
        """测试变量替换逻辑"""
        template_script = "echo 'Hello {{name}}! Your age is {{age}}'"
        variables = {"name": "Alice", "age": 30}
        
        command = template_script
        for var_name, var_value in variables.items():
            command = command.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        assert command == "echo 'Hello Alice! Your age is 30'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])