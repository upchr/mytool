# app/modules/acme/client.py
from .core import ACMEService

def issue_certificate(domains: list[str], email: str, dns_provider: str = "tencent"):
    acme = ACMEService(email=email)
    return acme.issue_certificate(domains, dns_provider)

def needs_renewal(cert_path: str, days_before: int = 30) -> bool:
    acme = ACMEService(email="dummy@example.com")
    return acme.needs_renewal(cert_path, days_before)
