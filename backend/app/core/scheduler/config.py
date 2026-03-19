# app/core/scheduler/config.py
import importlib
import logging
from typing import List

from app.core.scheduler import scheduler_service
from app.core.scheduler.base import JobProvider
logger = logging.getLogger(__name__)

# 集中配置所有提供者
PROVIDER_CONFIGS = [
    {
        'module_path': 'app.modules.cron.job_provider',
        'provider_name': 'cron_job_provider',
        'enabled': True
    },
    {
        'module_path': 'app.modules.workflow.job_provider',
        'provider_name': 'workflow_job_provider',
        'enabled': True
    },
    {
        'module_path': 'app.modules.acme.job_provider',
        'provider_name': 'ssl_job_provider',
        'enabled': True
    },
    # {
    #     'module_path': 'app.modules.cleanup.job_provider',
    #     'provider_name': 'cleanup_job_provider',
    #     'enabled': False  # 可以控制是否启用
    # }
]

def load_providers_from_config() -> List[JobProvider]:
    """从配置加载提供者"""
    providers = []

    for config in PROVIDER_CONFIGS:
        if not config.get('enabled', True):
            continue

        try:
            module = importlib.import_module(config['module_path'])
            provider = getattr(module, config['provider_name'])
            providers.append(provider)
            logger.info(f"⚙️ 从配置加载提供者: {provider.get_module_name()}")
        except Exception as e:
            logger.error(f"加载提供者 {config['module_path']} 失败: {e}")

    return providers

def init_schedule():
    # 从配置加载所有任务提供者
    providers = load_providers_from_config()

    # 注册所有提供者到调度器
    registered_count = 0
    for provider in providers:
        try:
            scheduler_service.register_provider(provider)
            registered_count += 1
            logger.info(f"✅ 已注册任务提供者: {provider.get_module_name()}")
        except Exception as e:
            logger.error(f"❌ 注册任务提供者失败: {e}")

    # 启动调度器
    scheduler_service.start()
    logger.info(f"✅ 调度器启动完成，共注册 {registered_count} 个提供者")

def destroy_schedule():
    scheduler_service.shutdown()
    logger.info("✅ 定时调度器已关闭")
