# app/modules/acme/client.py
from pathlib import Path
from app.modules.acme.core import ACMEService  # 改为绝对导入

def issue_certificate(domains: list[str], secret_id: str, secret_key: str, email: str, dns_provider: str = "tencent"):
    acme = ACMEService(email=email,secret_id=secret_id,secret_key=secret_key,dns_provider=dns_provider,staging=False)
    # acme = ACMEService(email=email,secret_id=secret_id,secret_key=secret_key,dns_provider=dns_provider)#测试
    return acme.issue_certificate(domains)

def needs_renewal(cert_path: str, days_before: int = 30) -> bool:
    return ACMEService.needs_renewal(cert_path, days_before)


