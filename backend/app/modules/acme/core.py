# app/modules/acme/core.py
import sys
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from acme import challenges
from acme.client import ClientV2, ClientNetwork
from acme.messages import Directory
from acme.errors import PollError
from josepy import JWKRSA

from app.modules.acme.dns_providers import get_dns_provider
import time
import logging
import re

logger = logging.getLogger(__name__)

def generate_csr(private_key, domains: list[str]):
    """生成 CSR"""
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domains[0])])
    csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
    san_list = [x509.DNSName(d) for d in domains]
    csr_builder = csr_builder.add_extension(x509.SubjectAlternativeName(san_list), critical=False)
    csr = csr_builder.sign(private_key, hashes.SHA256())
    return csr.public_bytes(Encoding.PEM)

class ACMEService:
    def __init__(self, email: str, staging: bool = True):
        self.email = email

        if sys.platform.startswith("win"):
            self.cert_dir = Path.cwd().parent.parent / "data/certs"
        else:
            # Linux / Docker 挂载卷
            self.cert_dir=Path("/toolsplus/data/certs")
        self.cert_dir.mkdir(exist_ok=True)

        # 使用 staging 环境用于测试，生产环境改为 False
        if staging:
            self.directory_url = "https://acme-staging-v02.api.letsencrypt.org/directory"
        else:
            self.directory_url = "https://acme-v02.api.letsencrypt.org/directory"

        self.account_key_path = self.cert_dir / "account_key.pem"
        self.account_key = self._load_or_create_account_key()

        # 初始化网络客户端
        self.net = ClientNetwork(self.account_key, user_agent="MyACME/1.0")

        # 获取目录
        logger.info(f"获取 ACME 目录: {self.directory_url}")
        directory = Directory.from_json(self.net.get(self.directory_url).json())
        self.client = ClientV2(directory, self.net)

        # 注册账户
        self._register_account()

    def _load_or_create_account_key(self):
        """加载或创建账户密钥"""
        if self.account_key_path.exists():
            logger.info(f"加载已有账户密钥: {self.account_key_path}")
            with open(self.account_key_path, "rb") as f:
                key = load_pem_private_key(f.read(), password=None)
            return JWKRSA(key=key)
        else:
            logger.info("生成新的账户密钥")
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            pem = key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
            with open(self.account_key_path, "wb") as f:
                f.write(pem)
            return JWKRSA(key=key)

    def _register_account(self):
        """注册或获取 ACME 账户"""
        from acme.messages import NewRegistration
        from acme import errors

        # 账户 URI 缓存文件
        account_uri_path = self.cert_dir / "account_uri.txt"

        # --- 第一步：尝试从缓存加载 ---
        if account_uri_path.exists():
            with open(account_uri_path, "r") as f:
                cached_uri = f.read().strip()
            logger.info(f"从缓存加载账户 URI: {cached_uri}")
            self.account_uri = cached_uri
            self.net.account = {"uri": cached_uri}
            return

        # --- 第二步：无缓存，尝试注册新账户 ---
        reg = NewRegistration.from_data(
            email=self.email,
            terms_of_service_agreed=True
        )

        try:
            # 尝试注册新账户
            self.registration = self.client.new_account(reg)
            account_uri = self.registration.uri
            logger.info(f"✅ 新账户注册成功: {account_uri}")

            # 保存 URI 到缓存
            with open(account_uri_path, "w") as f:
                f.write(account_uri)
            self.account_uri = account_uri
            self.net.account = {"uri": account_uri}

        except errors.ConflictError as e:
            # --- 第三步：账户已存在，提取 URI ---
            logger.info("⚠️ 账户已存在，正在提取 URI...")
            account_uri = None

            if hasattr(e, 'response') and e.response is not None:
                if hasattr(e.response, 'headers') and 'Location' in e.response.headers:
                    account_uri = e.response.headers['Location']
                    logger.debug("从 response.headers 提取成功")

            if not account_uri and hasattr(e, 'location'):
                account_uri = e.location
                logger.debug("从 e.location 提取成功")

            if not account_uri:
                match = re.search(r'(https?://[^\s]+)', str(e))
                if match:
                    account_uri = match.group(0)
                    logger.debug("从异常字符串提取成功")

            if not account_uri:
                logger.error("无法提取账户 URI")
                raise

            logger.info(f"成功提取账户 URI: {account_uri}")

            with open(account_uri_path, "w") as f:
                f.write(account_uri)
            self.account_uri = account_uri
            self.net.account = {"uri": account_uri}

        except Exception as e:
            logger.error(f"❌ 账户操作失败: {e}")
            raise

    def _check_challenge_results(self, authz):
        """
        检查挑战结果 - 使用 poll 方法 (符合 ClientV2 API)

        Returns:
            (is_valid, status, error_message)
        """
        try:
            # 使用 poll 方法查询授权状态 (ClientV2 API)
            updated_authz, response = self.client.poll(authz)

            # 获取状态值
            status = updated_authz.body.status
            # 处理可能的 Status 对象
            if hasattr(status, 'value'):
                status_str = status.value
            else:
                status_str = str(status)

            logger.info(f"授权状态: {status_str}")

            # 检查挑战状态
            for chall in updated_authz.body.challenges:
                if isinstance(chall.chall, challenges.DNS01):
                    chall_status = chall.status
                    # 处理可能的 Status 对象
                    if hasattr(chall_status, 'value'):
                        chall_status_str = chall_status.value
                    else:
                        chall_status_str = str(chall_status)

                    logger.info(f"DNS-01 挑战状态: {chall_status_str}")

                    # 如果挑战状态为 valid，返回成功
                    if chall_status_str == 'Status(valid)':
                        logger.info("✅ DNS-01 挑战验证成功")
                        return True, chall_status_str, None

                    # 如果挑战状态为 invalid，返回错误
                    if chall_status_str == 'Status(invalid)':
                        error_msg = str(chall.error) if chall.error else "挑战失败"
                        return False, chall_status_str, error_msg

            # 如果循环中没有返回，但授权状态为 valid，视为成功
            if status_str == 'Status(valid)':
                logger.info("✅ 授权状态为 valid，视为验证成功")
                return True, status_str, None

            # 其他情况视为失败
            logger.warning(f"挑战未完成，授权状态: {status_str}")
            return False, status_str, "挑战未完成"

        except Exception as e:
            logger.error(f"查询授权状态失败: {e}")
            return False, "error", str(e)

    def issue_certificate(self, domains: list[str], dns_provider: str = "tencent", wait_time: int = 60):
        """
        申请证书

        Args:
            domains: 域名列表，如 ['chrmjj.fun', '*.chrmjj.fun']
            dns_provider: DNS 提供商名称
            wait_time: DNS 生效等待时间（秒）

        Returns:
            (cert_path, key_path)
        """
        logger.info(f"开始申请证书: {domains}")

        # 生成域名私钥
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # 生成 CSR
        csr_pem = generate_csr(private_key, domains)

        # 创建订单
        logger.info("创建订单")
        order = self.client.new_order(csr_pem)

        # 处理所有授权
        dns_client = get_dns_provider(dns_provider)
        authz_records = []  # 保存记录ID用于清理
        challenge_results = []  # 保存每个域名的挑战结果

        try:
            for authz in order.authorizations:
                domain = authz.body.identifier.value
                logger.info(f"验证域名: {domain}")

                # 查找 DNS-01 挑战
                dns_challenge = None
                for chall in authz.body.challenges:
                    if isinstance(chall.chall, challenges.DNS01):
                        dns_challenge = chall
                        break

                if not dns_challenge:
                    raise Exception(f"未找到 DNS-01 挑战 for {domain}")

                # 计算验证值
                validation = dns_challenge.validation(self.client.net.key)
                record_name = dns_challenge.chall.validation_domain_name(domain)

                # 解析域名
                parts = record_name.split(".")
                if len(parts) > 2:
                    rr = ".".join(parts[:-2])
                    main_domain = ".".join(parts[-2:])
                else:
                    rr = "_acme-challenge"
                    main_domain = record_name.replace("_acme-challenge.", "")

                logger.info(f"添加 TXT 记录: {rr}.{main_domain} -> {validation}")

                # 调用 DNS 提供商添加记录
                record_id = dns_client.add_txt_record(main_domain, rr, validation)
                if not record_id:
                    raise Exception(f"添加 DNS 记录失败 for {domain}")

                authz_records.append((main_domain, record_id))

                # 等待 DNS 生效
                logger.info(f"等待 {wait_time} 秒让 DNS 生效")
                time.sleep(wait_time)

                # 回应挑战
                logger.info(f"回应挑战: {domain}")
                self.client.answer_challenge(dns_challenge, dns_challenge.response(self.client.net.key))

                # 等待一点时间让 Let's Encrypt 处理
                time.sleep(5)

                # 检查挑战结果
                is_valid, status, error = self._check_challenge_results(authz)
                challenge_results.append({
                    'domain': domain,
                    'is_valid': is_valid,
                    'status': status,
                    'error': error
                })

                if not is_valid:
                    logger.error(f"❌ 域名 {domain} 验证失败: {error}")
                else:
                    logger.info(f"✅ 域名 {domain} 验证成功")

            # 检查是否有失败的验证
            failed_domains = [r for r in challenge_results if not r['is_valid']]
            if failed_domains:
                error_msg = f"以下域名验证失败: {[r['domain'] for r in failed_domains]}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 轮询订单状态 - 使用 poll_and_finalize (ClientV2 API)
            logger.info("等待订单完成...")
            deadline = datetime.now() + timedelta(seconds=180)

            try:
                # 使用 poll_and_finalize 方法 (ClientV2 API)
                finalized_order = self.client.poll_and_finalize(order, deadline)
                logger.info("✅ 订单已完成")

            except PollError as e:
                logger.error(f"❌ 订单轮询失败: {e}")

            except Exception as e:
                logger.error(f"❌ 订单处理失败: {e}")
                raise

            # 获取证书
            logger.info("获取证书")

            # 方法1: 直接从 finalized_order 获取 (根据您的 ClientV2 实现)
            if hasattr(finalized_order, 'fullchain_pem') and finalized_order.fullchain_pem:
                cert_pem = finalized_order.fullchain_pem
                logger.info("✅ 证书已从订单获取")
            else:
                # 方法2: 通过证书 URL 获取 (根据您提供的源码)
                logger.info(f"从证书 URL 下载: {finalized_order.body.certificate}")
                cert_response = self.client._post_as_get(finalized_order.body.certificate)
                cert_pem = cert_response.text
                logger.info("✅ 证书下载成功")

            # 保存证书
            main_domain = domains[0].replace("*.", "")
            cert_path = self.cert_dir / f"{main_domain}.crt"
            key_path = self.cert_dir / f"{main_domain}.key"

            with open(cert_path, "w") as f:
                f.write(cert_pem)

            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    Encoding.PEM,
                    PrivateFormat.TraditionalOpenSSL,
                    NoEncryption()
                ))

            logger.info(f"✅ 证书已保存: {cert_path}")
            return str(cert_path), str(key_path)

        finally:
            # 清理 DNS 记录
            logger.info("清理 DNS 记录")
            for main_domain, record_id in authz_records:
                try:
                    dns_client.del_txt_record(main_domain, record_id)
                    logger.info(f"已删除记录: {record_id}")
                except Exception as e:
                    logger.error(f"删除记录失败 {record_id}: {e}")

    @staticmethod
    def needs_renewal(cert_path: str, days_before=30) -> bool:
        """检查证书是否需要续期"""
        if not Path(cert_path).exists():
            logger.info(f"证书不存在: {cert_path}")
            return True

        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())

        expiry = cert.not_valid_after
        now = datetime.now()
        days_left = (expiry - now).days
        logger.info(f"证书剩余 {days_left} 天")

        return now + timedelta(days=days_before) >= expiry


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    #
    # 创建 ACME 服务 - 使用生产环境
    acme = ACMEService(
        email="1017719268@qq.com",
        staging=True  # 生产环境
    )

    # 申请证书
    # domains = ["*.chrmjj.fun", "*.gulimall.chrmjj.fun", "chrmjj.fun"]  # 👈 修改这里
    domains = ["*.chrmjj.fun"]  # 👈 修改这里
    cert, key = acme.issue_certificate(
        domains,
        dns_provider="tencent",
        wait_time=30
    )

    print(f"\n✅ 证书生成成功!")
    print(f"证书: {cert}")
    print(f"密钥: {key}")

    # 检查续期
    if acme.needs_renewal(cert):
        print("需要续期")
    else:
        print("证书有效期充足")


    # # 检查续期
    # if ACMEService.needs_renewal(Path('P:\\workspace\\project\\mytool\\backend\\app\\data\\certs\\chrmjj.fun.crt')):
    #     print("需要续期")
    # else:
    #     print("证书有效期充足")
