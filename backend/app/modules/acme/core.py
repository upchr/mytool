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
import logging
import re
import time
import os

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
    def __init__(self, email: str, secret_id: str, secret_key: str, dns_provider: str, staging: bool = True):
        # 基础参数
        self.email = email
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.dns_provider = dns_provider

        # 生成路径
        from app.core.utils.path_utils import path_utils
        base_dir = path_utils.get_cert_dir()
        safe_email = self._safe_filename(self.email)
        # ✅ 隔离 staging/prod 账户缓存，避免冲突
        env_suffix = "staging" if staging else "prod"
        self.cert_dir = base_dir / f"{safe_email}_{env_suffix}"
        self.cert_dir.mkdir(exist_ok=True, parents=True)

        # 认证信息
        # ✅ 修复：去掉 URL 末尾空格（致命问题！）
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

    def _safe_filename(self, email: str) -> str:
        """将邮箱转换为安全的文件夹名"""
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
            self.registration = self.client.new_account(reg)
            account_uri = self.registration.uri
            logger.info(f"✅ 新账户注册成功: {account_uri}")

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

            if not account_uri and hasattr(e, 'location'):
                account_uri = e.location

            if not account_uri:
                match = re.search(r'(https?://[^\s]+)', str(e))
                if match:
                    account_uri = match.group(0)

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
        Returns: (is_valid, status, error_message)
        """
        try:
            updated_authz, response = self.client.poll(authz)
            status = updated_authz.body.status
            status_str = status.value if hasattr(status, 'value') else str(status)
            logger.info(f"授权状态: {status_str}")

            for chall in updated_authz.body.challenges:
                if isinstance(chall.chall, challenges.DNS01):
                    chall_status = chall.status
                    chall_status_str = chall_status.value if hasattr(chall_status, 'value') else str(chall_status)
                    logger.info(f"DNS-01 挑战状态: {chall_status_str}")

                    if chall_status_str == 'Status(valid)':
                        logger.info("✅ DNS-01 挑战验证成功")
                        return True, chall_status_str, None
                    if chall_status_str == 'Status(invalid)':
                        error_msg = str(chall.error) if chall.error else "挑战失败"
                        return False, chall_status_str, error_msg

            if status_str == 'Status(valid)':
                logger.info("✅ 授权状态为 valid，视为验证成功")
                return True, status_str, None

            logger.warning(f"挑战未完成，授权状态: {status_str}")
            return False, status_str, "挑战未完成"

        except Exception as e:
            logger.error(f"查询授权状态失败: {e}")
            return False, "error", str(e)

    def _wait_dns_propagation(self, record_name: str, expected_value: str, timeout: int = 120):
        """
        ✅ 新增：主动探测 DNS 生效（生产环境推荐）
        轮询公共 DNS 直到记录生效，避免固定等待时间不足或过长
        """
        try:
            import dns.resolver
        except ImportError:
            logger.warning("⚠️ dnspython 未安装，使用固定等待时间")
            time.sleep(60)
            return True

        start = time.time()
        resolvers = ['8.8.8.8', '1.1.1.1', '223.5.5.5']  # Google, Cloudflare, 阿里 DNS

        while time.time() - start < timeout:
            for resolver_ip in resolvers:
                try:
                    answers = dns.resolver.resolve(record_name, 'TXT', nameserver=[resolver_ip], lifetime=5)
                    if any(expected_value in str(rdata) for rdata in answers):
                        logger.info(f"✅ DNS 记录已生效 ({resolver_ip}): {record_name}")
                        return True
                except Exception:
                    pass  # 尝试下一个 DNS
            time.sleep(5)

        logger.warning(f"⚠️ DNS 传播可能未完成，继续尝试验证: {record_name}")
        return True  # 不阻塞流程，让 Let's Encrypt 自己重试

    def issue_certificate(self, domains: list[str], wait_time: int = 60):
        """
        申请证书 - 修复版，支持泛域名+主域名共用记录 + 跳过已验证授权 + 多 validation 值

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

        # 初始化 DNS 客户端
        dns_client = get_dns_provider(self.dns_provider, self.secret_id, self.secret_key)

        # ========== 数据结构定义 ==========
        # challenge_map: 唯一授权键 -> 挑战详情（用于回应挑战）
        # key: authz.uri（唯一标识每个 authorization）
        challenge_map: dict[str, dict] = {}

        # dns_records: record_key -> DNS 记录信息（用于添加/清理记录）
        # key: f"{main_domain}:{rr}"
        dns_records: dict[str, dict] = {}

        try:
            # ========== 第一步：收集所有需要验证的域名及其验证信息 ==========
            logger.info("第一步：收集所有需要验证的域名信息")
            for authz in order.authorizations:
                identifier = authz.body.identifier.value
                is_wildcard = bool(authz.body.wildcard)
                display_name = f"*.{identifier}" if is_wildcard else identifier
                logger.info(f"需要验证的域名: {display_name} (wildcard={is_wildcard})")

                # ✅ 优化1: 跳过已有效的授权（避免重复验证，提升效率）
                authz_status = authz.body.status
                if hasattr(authz_status, 'value'):
                    authz_status = authz_status.value
                if authz_status == "valid":
                    logger.info(f"⏭️ {display_name} 授权已有效，跳过")
                    continue

                # 查找 DNS-01 挑战
                dns_challenge = None
                for chall in authz.body.challenges:
                    if isinstance(chall.chall, challenges.DNS01):
                        dns_challenge = chall
                        break

                if not dns_challenge:
                    raise Exception(f"未找到 DNS-01 挑战 for {display_name}")

                # 计算验证值和记录名称
                validation = dns_challenge.validation(self.client.net.key)
                record_name = dns_challenge.chall.validation_domain_name(identifier)

                # 解析 record_name -> rr + main_domain
                parts = record_name.split(".")
                if len(parts) > 2:
                    rr = ".".join(parts[:-2])
                    main_domain = ".".join(parts[-2:])
                else:
                    rr = "_acme-challenge"
                    main_domain = record_name.replace("_acme-challenge.", "")

                # ✅ 优化2: 使用唯一键防止泛域名+主域名覆盖
                # 方案: 使用 authz.uri 作为唯一键（最可靠，每个 authorization 唯一）
                map_key = authz.uri

                challenge_map[map_key] = {
                    'identifier': identifier,
                    'is_wildcard': is_wildcard,
                    'display_name': display_name,
                    'authz': authz,
                    'challenge': dns_challenge,
                    'validation': validation,
                    'main_domain': main_domain,
                    'rr': rr,
                    'record_name': record_name,
                    'record_key': f"{main_domain}:{rr}"  # 用于 DNS 记录去重
                }
                logger.info(f"域名 {display_name} 的验证信息: {rr}.{main_domain} -> {validation}")

            # 如果没有需要验证的域名（全部已有效），直接跳过 DNS 操作
            if not challenge_map:
                logger.info("⏭️ 所有域名授权已有效，跳过 DNS 验证流程")
            else:
                # ========== 第二步：按 record_key 分组，支持多 validation 值 ==========
                logger.info("第二步：添加 DNS TXT 记录")
                records_group: dict[str, dict] = {}

                for map_key, info in challenge_map.items():
                    record_key = info['record_key']
                    if record_key not in records_group:
                        records_group[record_key] = {
                            'main_domain': info['main_domain'],
                            'rr': info['rr'],
                            'validations': [],  # ✅ 优化3: 支持多 validation 值（健壮性保障）
                            'identifiers': []
                        }
                    # 去重添加 validation（同订单通常相同，但保留健壮性）
                    if info['validation'] not in records_group[record_key]['validations']:
                        records_group[record_key]['validations'].append(info['validation'])
                    records_group[record_key]['identifiers'].append(info['display_name'])

                # 为每个唯一记录添加 DNS 记录
                for record_key, group in records_group.items():
                    main_domain = group['main_domain']
                    rr = group['rr']
                    validations = group['validations']
                    identifiers = group['identifiers']

                    logger.info(f"添加 TXT 记录: {rr}.{main_domain} -> {validations} (用于 {len(identifiers)} 个域名: {identifiers})")

                    # ✅ 优化4: 腾讯云支持单条记录多值，循环添加会自动合并
                    record_ids = []
                    for validation in validations:
                        record_id = dns_client.add_txt_record(main_domain, rr, validation)
                        if not record_id:
                            raise Exception(f"添加 DNS 记录失败 for {record_key}")
                        record_ids.append(record_id)
                        logger.info(f"  └─ 添加 validation: {validation[:20]}... -> RecordId: {record_id}")

                    # 保存记录信息（保存所有 record_id 用于清理）
                    dns_records[record_key] = {
                        'record_ids': record_ids,  # ✅ 保存所有 ID
                        'main_domain': main_domain,
                        'rr': rr,
                        'validations': validations,
                        'identifiers': identifiers
                    }
                    logger.info(f"✅ 添加成功，记录数: {len(record_ids)}")

                # ========== 第三步：等待 DNS 生效 ==========
                # ✅ 优化5: 优先使用主动探测，降级为固定等待
                first_record = next(iter(records_group.values()))
                record_name = f"{first_record['rr']}.{first_record['main_domain']}"
                first_validation = first_record['validations'][0]

                logger.info(f"第三步：等待 DNS 生效")
                self._wait_dns_propagation(record_name, first_validation, timeout=wait_time)

                # ========== 第四步：回应所有挑战 ==========
                logger.info("第四步：回应所有挑战")
                for map_key, info in challenge_map.items():
                    logger.info(f"回应挑战: {info['display_name']}")
                    self.client.answer_challenge(
                        info['challenge'],
                        info['challenge'].response(self.client.net.key)
                    )

                # 等待 Let's Encrypt 处理
                logger.info("等待 Let's Encrypt 处理...")
                time.sleep(10)

                # ========== 第五步：检查所有挑战结果（带重试） ==========
                logger.info("第五步：检查挑战结果")
                successful_keys = set()
                # ✅ 优化6: 生产环境增加重试次数和间隔
                max_retries = 6 if not self.directory_url.startswith("https://acme-staging") else 3
                retry_interval = 30 if not self.directory_url.startswith("https://acme-staging") else 10

                for retry in range(max_retries):
                    if retry > 0:
                        logger.info(f"🔄 第 {retry}/{max_retries} 次重试检查挑战结果...")
                        time.sleep(retry_interval)

                    pending_keys = []
                    for map_key, info in challenge_map.items():
                        if map_key in successful_keys:
                            continue

                        logger.info(f"检查域名 {info['display_name']} 的验证结果")
                        is_valid, status, error = self._check_challenge_results(info['authz'])

                        if is_valid:
                            logger.info(f"✅ {info['display_name']} 验证成功")
                            successful_keys.add(map_key)
                        else:
                            # 区分"处理中"和"真正失败"
                            if error and "pending" not in str(error).lower() and "处理中" not in error:
                                logger.error(f"❌ {info['display_name']} 验证失败: {error}")
                                pending_keys.append({'display_name': info['display_name'], 'error': error})
                            else:
                                logger.info(f"⏳ {info['display_name']} 仍在处理中: {status}")

                    # 全部成功则提前退出
                    if len(successful_keys) == len(challenge_map):
                        break

                # 检查最终结果
                if len(successful_keys) != len(challenge_map):
                    failed = [info['display_name'] for k, info in challenge_map.items() if k not in successful_keys]
                    error_msg = f"以下域名验证失败/超时: {failed}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            # ========== 第六步：轮询订单状态并获取证书 ==========
            logger.info("第六步：等待订单完成...")
            deadline = datetime.now() + timedelta(seconds=180)

            try:
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
            if hasattr(finalized_order, 'fullchain_pem') and finalized_order.fullchain_pem:
                cert_pem = finalized_order.fullchain_pem
                logger.info("✅ 证书已从订单获取")
            else:
                logger.info(f"从证书 URL 下载: {finalized_order.body.certificate}")
                cert_response = self.client._post_as_get(finalized_order.body.certificate)
                cert_pem = cert_response.text
                logger.info("✅ 证书下载成功")

            # ========== 第八步：保存证书 ==========
            logger.info("第八步：保存证书")
            main_domain = domains[0].replace("*.", "")
            date_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

            cert_path = self.cert_dir / f"{main_domain}_{date_suffix}.crt"
            key_path = self.cert_dir / f"{main_domain}_{date_suffix}.key"

            with open(cert_path, "w", encoding="utf-8") as f:
                f.write(cert_pem)
            logger.info(f"✅ 证书已保存: {cert_path}")

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
            # ========== 第九步：清理 DNS 记录（去重 + 多 ID 支持） ==========
            if dns_records:
                logger.info("第九步：清理 DNS 记录")
                cleaned = set()
                for record_key, info in dns_records.items():
                    if record_key not in cleaned:
                        for record_id in info.get('record_ids', [info.get('record_id')]):
                            if record_id:
                                try:
                                    dns_client.del_txt_record(info['main_domain'], record_id)
                                    logger.info(f"✅ 已删除记录 {record_id} (用于 {info['identifiers']})")
                                except Exception as e:
                                    logger.error(f"❌ 删除记录失败 {record_id}: {e}")
                        cleaned.add(record_key)
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
            return 0  # ✅ 修复：返回 0 而非 True

        try:
            with open(cert_path_obj, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            expiry = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after
            now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()
            days_left = (expiry - now).days
            logger.info(f"证书剩余 {days_left} 天")

            return days_left
        except Exception as e:
            logger.error(f"检查证书续期失败: {e}")
            return 0
