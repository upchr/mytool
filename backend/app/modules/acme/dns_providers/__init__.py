# app/modules/acme/dns_providers/__init__.py
from abc import ABC, abstractmethod

class DnsProvider(ABC):
    def __init__(self, secret_id: str, secret_key: str):
        self.secret_id = secret_id
        self.secret_key = secret_key

    @abstractmethod
    def add_txt_record(self, domain: str, sub_domain: str, value: str):
        """添加 TXT 记录"""
        pass

    @abstractmethod
    def del_txt_record(self, domain: str, record_id: str):
        """删除 TXT 记录（可选）"""
        pass

def get_dns_provider(provider: str,secret_id: str,secret_key: str) -> DnsProvider:
    if provider == "tencent":
        from .tencent import TencentDnsProvider
        return TencentDnsProvider(secret_id=secret_id,secret_key=secret_key)
    else:
        raise ValueError(f"暂不支持该DNS提供商: {provider}")
