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
import subprocess
import time

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
    def __init__(self, email: str,secret_id: str,secret_key: str,dns_provider: str, staging: bool = True):
        # 基础参数
        self.email = email
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.dns_provider = dns_provider

        # 生成路径
        from app.core.utils.path_utils import path_utils
        base_dir=path_utils.get_cert_dir()
        safe_email = self._safe_filename(self.email)
        self.cert_dir = base_dir / safe_email
        self.cert_dir.mkdir(exist_ok=True, parents=True)

        # 认证信息
        if staging:
            # 使用 staging 环境用于测试，生产环境改为 False
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

    def _safe_filename(self, email: str) -> str:
        """将邮箱转换为安全的文件夹名"""
        # 替换 @ 和 . 为下划线
        return email.replace('@', '_at_').replace('.', '_dot_')

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

    # def issue_certificate(self, domains: list[str], wait_time: int = 60):
    #     """
    #     申请证书 - 优化版本，使用字典记录域名和记录的关系
    #
    #     Args:
    #         domains: 域名列表，如 ['chrmjj.fun', '*.chrmjj.fun']
    #         wait_time: DNS 生效等待时间（秒）
    #
    #     Returns:
    #         (cert_path, key_path)
    #     """
    #     logger.info(f"开始申请证书: {domains}")
    #
    #     # 生成域名私钥
    #     private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    #
    #     # 生成 CSR
    #     csr_pem = generate_csr(private_key, domains)
    #
    #     # 创建订单
    #     logger.info("创建订单")
    #     order = self.client.new_order(csr_pem)
    #
    #     # 处理所有授权
    #     dns_client = get_dns_provider(self.dns_provider, self.secret_id, self.secret_key)
    #
    #     # 使用字典记录 DNS 记录 -> 挑战信息
    #     # key: DNS记录的唯一标识 (如 "_acme-challenge.chrmjj.fun")
    #     # value: {
    #     #   'record_id': DNS记录ID,
    #     #   'main_domain': 主域名,
    #     #   'rr': 记录名称,
    #     #   'validation': 验证值,
    #     #   'challenges': 挑战列表, 每个挑战包含 {identifier, authz, challenge}
    #     # }
    #     dns_records = {}
    #
    #     # 使用字典记录域名 -> 挑战信息 (用于日志和错误处理)
    #     challenge_map = {}
    #
    #     try:
    #         # ========== 第一步：收集所有需要验证的域名及其验证信息 ==========
    #         logger.info("第一步：收集所有需要验证的域名信息")
    #         for authz in order.authorizations:
    #             identifier = authz.body.identifier.value  # 可能是 "chrmjj.fun" 或 "*.chrmjj.fun"
    #             logger.info(f"需要验证的域名: {identifier}")
    #             if identifier  in challenge_map:
    #                 logger.info(f"重复，跳过验证的域名: {identifier}")
    #                 continue
    #
    #             # 查找 DNS-01 挑战
    #             dns_challenge = None
    #             for chall in authz.body.challenges:
    #                 if isinstance(chall.chall, challenges.DNS01):
    #                     dns_challenge = chall
    #                     break
    #
    #             if not dns_challenge:
    #                 raise Exception(f"未找到 DNS-01 挑战 for {identifier}")
    #
    #             # 计算验证值
    #             validation = dns_challenge.validation(self.client.net.key)
    #
    #             # 计算记录名称
    #             record_name = dns_challenge.chall.validation_domain_name(identifier)
    #
    #             # 解析域名
    #             parts = record_name.split(".")
    #             if len(parts) > 2:
    #                 rr = ".".join(parts[:-2])
    #                 main_domain = ".".join(parts[-2:])
    #             else:
    #                 rr = "_acme-challenge"
    #                 main_domain = record_name.replace("_acme-challenge.", "")
    #
    #             # 创建 DNS 记录的唯一键
    #             record_key = f"{main_domain}:{rr}"
    #
    #             # 保存挑战信息到 challenge_map。覆盖取最后一次。
    #             challenge_map[identifier] = {
    #                 'authz': authz,
    #                 'challenge': dns_challenge,
    #                 'validation': validation,
    #                 'main_domain': main_domain,
    #                 'rr': rr,
    #                 'record_name': record_name,
    #                 'record_key': record_key
    #             }
    #
    #             logger.info(f"域名 {identifier} 的验证信息: {rr}.{main_domain} -> {validation}")
    #         # ========== 第二步：为每个唯一的 DNS 记录添加 TXT 记录 ==========
    #         logger.info("第二步：添加 DNS TXT 记录")
    #
    #         # 按 record_key 分组
    #         records_group = {}
    #         for identifier, info in challenge_map.items():
    #             record_key = info['record_key']
    #             if record_key not in records_group:
    #                 records_group[record_key] = {
    #                     'main_domain': info['main_domain'],
    #                     'rr': info['rr'],
    #                     'validation': info['validation'],
    #                     'identifiers': []
    #                 }
    #             records_group[record_key]['identifiers'].append(identifier)
    #
    #         # 为每个唯一记录添加 DNS 记录
    #         for record_key, group_info in records_group.items():
    #             main_domain = group_info['main_domain']
    #             rr = group_info['rr']
    #             validation = group_info['validation']
    #             identifiers = group_info['identifiers']
    #
    #             logger.info(f"添加 TXT 记录: {rr}.{main_domain} -> {validation} (用于 {len(identifiers)} 个域名: {identifiers})")
    #
    #             # 调用 DNS 提供商添加记录（只添加一次）
    #             record_id = dns_client.add_txt_record(main_domain, rr, validation)
    #             if not record_id:
    #                 raise Exception(f"添加 DNS 记录失败 for {record_key}")
    #
    #             # 保存记录信息
    #             dns_records[record_key] = {
    #                 'record_id': record_id,
    #                 'main_domain': main_domain,
    #                 'rr': rr,
    #                 'validation': validation,
    #                 'identifiers': identifiers
    #             }
    #
    #             logger.info(f"✅ 添加成功，记录ID: {record_id}")
    #         # ========== 第三步：等待 DNS 生效（只需等待一次） ==========
    #         if dns_records:
    #             logger.info(f"第三步：等待 {wait_time} 秒让 DNS 生效")
    #             time.sleep(wait_time)
    #
    #         # ========== 第四步：回应所有挑战 ==========
    #         logger.info("第四步：回应所有挑战")
    #         for identifier, info in challenge_map.items():
    #             logger.info(f"回应挑战: {identifier}")
    #             self.client.answer_challenge(
    #                 info['challenge'],
    #                 info['challenge'].response(self.client.net.key)
    #             )
    #
    #         # 等待 Let's Encrypt 处理
    #         logger.info("等待 Let's Encrypt 处理...")
    #         time.sleep(10)
    #
    #         # ========== 第五步：检查所有挑战结果 ==========
    #         logger.info("第五步：检查挑战结果")
    #         failed_domains = []
    #         successful_domains = []
    #
    #         # 最多重试3次，每次间隔10秒
    #         max_retries = 3
    #         for retry in range(max_retries):
    #             if retry > 0:
    #                 logger.info(f"第 {retry} 次重试检查挑战结果...")
    #                 time.sleep(10)
    #
    #             failed_domains = []
    #             successful_domains = []
    #
    #             for identifier, info in challenge_map.items():
    #                 # 如果已经成功，跳过
    #                 if identifier in successful_domains:
    #                     continue
    #
    #                 logger.info(f"检查域名 {identifier} 的验证结果")
    #                 is_valid, status, error = self._check_challenge_results(info['authz'])
    #
    #                 if is_valid:
    #                     logger.info(f"✅ 域名 {identifier} 验证成功")
    #                     successful_domains.append(identifier)
    #                 else:
    #                     # 如果不是最终失败，暂时不标记为失败
    #                     if error and "处理中" not in error and "pending" not in error.lower():
    #                         logger.error(f"❌ 域名 {identifier} 验证失败: {error}")
    #                         failed_domains.append({
    #                             'domain': identifier,
    #                             'error': error
    #                         })
    #                     else:
    #                         logger.info(f"⏳ 域名 {identifier} 仍在处理中: {status}")
    #
    #             # 如果所有域名都成功了，跳出循环
    #             if len(successful_domains) == len(challenge_map):
    #                 break
    #
    #         # 检查是否有失败的验证
    #         if failed_domains:
    #             error_msg = f"以下域名验证失败: {[f['domain'] for f in failed_domains]}"
    #             logger.error(error_msg)
    #             raise Exception(error_msg)
    #
    #         # 检查是否所有域名都成功了
    #         if len(successful_domains) != len(challenge_map):
    #             missing = set(challenge_map.keys()) - set(successful_domains)
    #             error_msg = f"以下域名验证超时: {missing}"
    #             logger.error(error_msg)
    #             raise Exception(error_msg)
    #
    #         # ========== 第六步：轮询订单状态并获取证书 ==========
    #         logger.info("第六步：等待订单完成...")
    #         deadline = datetime.now() + timedelta(seconds=180)
    #
    #         try:
    #             # 使用 poll_and_finalize 方法 (ClientV2 API)
    #             finalized_order = self.client.poll_and_finalize(order, deadline)
    #             logger.info("✅ 订单已完成")
    #
    #         except PollError as e:
    #             logger.error(f"❌ 订单轮询失败: {e}")
    #             raise
    #
    #         except Exception as e:
    #             logger.error(f"❌ 订单处理失败: {e}")
    #             raise
    #
    #         # ========== 第七步：获取证书 ==========
    #         logger.info("第七步：获取证书")
    #
    #         # 方法1: 直接从 finalized_order 获取
    #         if hasattr(finalized_order, 'fullchain_pem') and finalized_order.fullchain_pem:
    #             cert_pem = finalized_order.fullchain_pem
    #             logger.info("✅ 证书已从订单获取")
    #         else:
    #             # 方法2: 通过证书 URL 获取
    #             logger.info(f"从证书 URL 下载: {finalized_order.body.certificate}")
    #             cert_response = self.client._post_as_get(finalized_order.body.certificate)
    #             cert_pem = cert_response.text
    #             logger.info("✅ 证书下载成功")
    #
    #         # ========== 第八步：保存证书 ==========
    #         # 提取主域名（去掉通配符）
    #         logger.info("第八步：保存证书")
    #         main_domain = domains[0].replace("*.", "")
    #         date_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    #
    #         cert_path = self.cert_dir / f"{main_domain}_{date_suffix}.crt"
    #         key_path = self.cert_dir / f"{main_domain}_{date_suffix}.key"
    #
    #         # 保存证书
    #         with open(cert_path, "w") as f:
    #             f.write(cert_pem)
    #         logger.info(f"✅ 证书已保存: {cert_path}")
    #
    #         # 保存私钥
    #         with open(key_path, "wb") as f:
    #             f.write(private_key.private_bytes(
    #                 Encoding.PEM,
    #                 PrivateFormat.TraditionalOpenSSL,
    #                 NoEncryption()
    #             ))
    #         logger.info(f"✅ 私钥已保存: {key_path}")
    #
    #         logger.info(f"✅ 证书申请成功完成!")
    #         return str(cert_path), str(key_path)
    #
    #     except Exception as e:
    #         logger.error(f"❌ 证书申请失败: {e}")
    #         raise
    #
    #     finally:
    #         # ========== 第九步：清理 DNS 记录 ==========
    #         if dns_records:
    #             logger.info("第九步：清理 DNS 记录")
    #             # 按记录去重清理
    #             cleaned_records = set()
    #             for record_key, info in dns_records.items():
    #                 if record_key not in cleaned_records:
    #                     try:
    #                         dns_client.del_txt_record(info['main_domain'], info['record_id'])
    #                         logger.info(f"✅ 已删除记录: {info['record_id']} (用于 {info['identifiers']})")
    #                         cleaned_records.add(record_key)
    #                     except Exception as e:
    #                         logger.error(f"❌ 删除记录失败 {info['record_id']}: {e}")
    #         else:
    #             logger.info("没有需要清理的 DNS 记录")
    def issue_certificate(self, domains: list[str], wait_time: int = 60):
        """
        申请证书 - 优化版本，使用字典记录域名和记录的关系

        Args:
            domains: 域名列表，如 ['chrmjj.fun', '*.chrmjj.fun']
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
        dns_client = get_dns_provider(self.dns_provider, self.secret_id, self.secret_key)

        # 使用字典记录 DNS 记录 -> 挑战信息
        # key: DNS记录的唯一标识 (如 "_acme-challenge.chrmjj.fun")
        # value: {
        #   'record_id': DNS记录ID,
        #   'main_domain': 主域名,
        #   'rr': 记录名称,
        #   'validation': 验证值,
        #   'challenges': 挑战列表, 每个挑战包含 {identifier, authz, challenge}
        # }
        dns_records = {}

        # 使用字典记录域名 -> 挑战信息 (用于日志和错误处理)
        challenge_map = {}

        try:
            # ========== 第一步：收集所有需要验证的域名及其验证信息 ==========
            logger.info("第一步：收集所有需要验证的域名信息")
            for authz in order.authorizations:
                identifier = authz.body.identifier.value  # 可能是 "chrmjj.fun" 或 "*.chrmjj.fun"
                logger.info(f"需要验证的域名: {identifier}")
                if identifier  in challenge_map:
                    logger.info(f"重复，跳过验证的域名: {identifier}")
                    continue

                # 查找 DNS-01 挑战
                dns_challenge = None
                for chall in authz.body.challenges:
                    if isinstance(chall.chall, challenges.DNS01):
                        dns_challenge = chall
                        break

                if not dns_challenge:
                    raise Exception(f"未找到 DNS-01 挑战 for {identifier}")

                # 计算验证值
                validation = dns_challenge.validation(self.client.net.key)

                # 计算记录名称
                record_name = dns_challenge.chall.validation_domain_name(identifier)

                # 解析域名
                parts = record_name.split(".")
                if len(parts) > 2:
                    rr = ".".join(parts[:-2])
                    main_domain = ".".join(parts[-2:])
                else:
                    rr = "_acme-challenge"
                    main_domain = record_name.replace("_acme-challenge.", "")

                # 创建 DNS 记录的唯一键
                record_key = f"{rr}:{main_domain}"

                # 保存挑战信息到 challenge_map。覆盖取最后一次。
                challenge_map[identifier] = {
                    'authz': authz,
                    'challenge': dns_challenge,
                    'validation': validation,
                    'main_domain': main_domain,
                    'rr': rr,
                    'record_name': record_name,
                    'record_key': record_key
                }

                logger.info(f"域名 {identifier} 的验证信息: {record_key} -> {validation}")
            # ========== 第二步：为每个唯一的 DNS 记录添加 TXT 记录 ==========
            logger.info("第二步：添加 DNS TXT 记录")
            for identifier, info in challenge_map.items():
                main_domain = info['main_domain']
                rr = info['rr']
                validation = info['validation']
                record_key = info['record_key']

                logger.info(f"添加 TXT 记录: {record_key} -> {validation} (用于域名: {identifier})")

                # 调用 DNS 提供商添加记录（只添加一次）
                record_id = dns_client.add_txt_record(main_domain, rr, validation)
                if not record_id:
                    raise Exception(f"添加 DNS 记录失败 for {record_key}")

                # 保存记录信息
                dns_records[record_key] = {
                    'record_id': record_id,
                    'main_domain': main_domain,
                    'rr': rr,
                    'validation': validation,
                    'identifier': identifier
                }

                logger.info(f"✅ 添加成功，记录ID: {record_id}")
            # ========== 第三步：等待 DNS 生效（只需等待一次） ==========
            if dns_records:
                logger.info(f"第三步：等待 {wait_time} 秒让 DNS 生效")
                time.sleep(wait_time)

            # ========== 第四步：回应所有挑战 ==========
            logger.info("第四步：回应所有挑战")
            for identifier, info in challenge_map.items():
                logger.info(f"回应挑战: {identifier}")
                self.client.answer_challenge(
                    info['challenge'],
                    info['challenge'].response(self.client.net.key)
                )

            # 等待 Let's Encrypt 处理
            logger.info("等待 Let's Encrypt 处理...")
            time.sleep(10)

            # ========== 第五步：检查所有挑战结果 ==========
            logger.info("第五步：检查挑战结果")
            failed_domains = []
            successful_domains = []

            # 最多重试3次，每次间隔10秒
            max_retries = 3
            for retry in range(max_retries):
                if retry > 0:
                    logger.info(f"第 {retry} 次重试检查挑战结果...")
                    time.sleep(10)

                failed_domains = []
                successful_domains = []

                for identifier, info in challenge_map.items():
                    # 如果已经成功，跳过
                    if identifier in successful_domains:
                        continue

                    logger.info(f"检查域名 {identifier} 的验证结果")
                    is_valid, status, error = self._check_challenge_results(info['authz'])

                    if is_valid:
                        logger.info(f"✅ 域名 {identifier} 验证成功")
                        successful_domains.append(identifier)
                    else:
                        # 如果不是最终失败，暂时不标记为失败
                        if error and "处理中" not in error and "pending" not in error.lower():
                            logger.error(f"❌ 域名 {identifier} 验证失败: {error}")
                            failed_domains.append({
                                'domain': identifier,
                                'error': error
                            })
                        else:
                            logger.info(f"⏳ 域名 {identifier} 仍在处理中: {status}")

                # 如果所有域名都成功了，跳出循环
                if len(successful_domains) == len(challenge_map):
                    break

            # 检查是否有失败的验证
            if failed_domains:
                error_msg = f"以下域名验证失败: {[f['domain'] for f in failed_domains]}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 检查是否所有域名都成功了
            if len(successful_domains) != len(challenge_map):
                missing = set(challenge_map.keys()) - set(successful_domains)
                error_msg = f"以下域名验证超时: {missing}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # ========== 第六步：轮询订单状态并获取证书 ==========
            logger.info("第六步：等待订单完成...")
            deadline = datetime.now() + timedelta(seconds=180)

            try:
                # 使用 poll_and_finalize 方法 (ClientV2 API)
                finalized_order = self.client.poll_and_finalize(order, deadline)
                logger.info("✅ 订单已完成")

            except PollError as e:
                logger.error(f"❌ 订单轮询失败: {e}")
                raise

            except Exception as e:
                logger.error(f"❌ 订单处理失败: {e}")
                raise

            # ========== 第七步：获取证书 ==========
            logger.info("第七步：获取证书")

            # 方法1: 直接从 finalized_order 获取
            if hasattr(finalized_order, 'fullchain_pem') and finalized_order.fullchain_pem:
                cert_pem = finalized_order.fullchain_pem
                logger.info("✅ 证书已从订单获取")
            else:
                # 方法2: 通过证书 URL 获取
                logger.info(f"从证书 URL 下载: {finalized_order.body.certificate}")
                cert_response = self.client._post_as_get(finalized_order.body.certificate)
                cert_pem = cert_response.text
                logger.info("✅ 证书下载成功")

            # ========== 第八步：保存证书 ==========
            # 提取主域名（去掉通配符）
            logger.info("第八步：保存证书")
            main_domain = domains[0].replace("*.", "")
            date_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

            cert_path = self.cert_dir / f"{main_domain}_{date_suffix}.crt"
            key_path = self.cert_dir / f"{main_domain}_{date_suffix}.key"

            # 保存证书
            with open(cert_path, "w") as f:
                f.write(cert_pem)
            logger.info(f"✅ 证书已保存: {cert_path}")

            # 保存私钥
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    Encoding.PEM,
                    PrivateFormat.TraditionalOpenSSL,
                    NoEncryption()
                ))
            logger.info(f"✅ 私钥已保存: {key_path}")

            logger.info(f"✅ 证书申请成功完成!")
            return str(cert_path), str(key_path)

        except Exception as e:
            logger.error(f"❌ 证书申请失败: {e}")
            raise

        finally:
            # ========== 第九步：清理 DNS 记录 ==========
            if dns_records:
                logger.info("第九步：清理 DNS 记录")
                # 按记录去重清理
                cleaned_records = set()
                for record_key, info in dns_records.items():
                    if record_key not in cleaned_records:
                        try:
                            dns_client.del_txt_record(info['main_domain'], info['record_id'])
                            logger.info(f"✅ 已删除TXT记录: {info['record_id']} (用于 {info['identifier']})")
                            cleaned_records.add(record_key)
                        except Exception as e:
                            logger.error(f"❌ 删除记录失败 {info['record_id']}: {e}")
            else:
                logger.info("没有需要清理的 DNS 记录")

    @staticmethod
    def needs_renewal(cert_path: str, days_before=30) -> bool:
        """检查证书是否需要续期"""
        try:
            left_days = ACMEService.left_days(cert_path)
            return left_days - days_before < 0
        except Exception as e:
            logger.error(f"检查证书续期失败: {e}")
            return True

    @staticmethod
    def left_days(cert_path: str) -> int:
        cert_path_obj = Path(cert_path)

        if not cert_path_obj.exists():
            logger.info(f"证书不存在: {cert_path}")
            return True

        try:
            with open(cert_path_obj, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            expiry = cert.not_valid_after
            now = datetime.now()
            days_left = (expiry + timedelta(hours=9) - now).days
            logger.info(f"证书剩余 {days_left} 天")

            return days_left
        except Exception as e:
            logger.error(f"检查证书续期失败: {e}")
            return 0
