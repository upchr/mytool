# -*- coding: utf-8 -*-
"""dianbiao 模块 - 采集接收 / 查询 API

API:
  POST /dianbiao/readings              采集端(蓝牙 PC)上报一条采样 → 幂等入库
  GET  /dianbiao/agent/config          采集端拉取运行配置(mytool 反向下发: 采集间隔/启停)
  GET  /dianbiao/readings              按电表+时间范围查询曲线数据(前端画图用)
  GET  /dianbiao/latest                刚表最新一条
  GET  /dianbiao/meters                设备列表
  GET  /dianbiao/stats                 按日/周/月/季/年聚合统计
  GET  /dianbiao/collector-configs     采集器配置列表(面板维护)
  PUT  /dianbiao/collector-configs     保存采集器配置(反向下发)
  GET  /dianbiao/triggers              采集器部署触发器列表(节点+目录搭建)
  POST /dianbiao/triggers              搭建触发器(所属节点+采集目录+参数)
  POST /dianbiao/triggers/{id}/init    初始化: 远端跑 dianbiao doctor, 通过后反推基线配置
  PUT  /dianbiao/triggers/{id}         更新触发器(启停/间隔)并反推配置到采集器
  DELETE /dianbiao/triggers/{id}       删除触发器
  GET  /dianbiao/tokens                推送 Token 列表(面板维护)
  POST /dianbiao/tokens                创建推送 Token
  POST /dianbiao/tokens/{id}/revoke     作废 Token(采集端立即失效)

认证:
  /readings 上报与 /agent/config 拉取受 X-Agent-Token 保护(public_paths 放行 + 此处查库校验);
  Token 在 dianbiao_token 表维护(浏览器页面可创建/作废, 不依赖环境变量);
  其余查询/管理接口走全局 JWT。
"""
import json
import io
import logging
import os
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.db.database import engine
from app.core.pojo.response import BaseResponse
from app.core.exception.exceptions import UnauthorizedException, NotFoundException
from app.modules.node.models import nodes_table
from app.modules.node.schemas import NodeRead
from app.core.sh.ssh_client import SSHClient

from . import schemas
from .models import (
    dianbiao_reading_table, dianbiao_token_table, dianbiao_collector_config_table,
    dianbiao_trigger_table, dianbiao_alert_table, dianbiao_charge_table,
)
from app.modules.notify.models import notification_services_table
from app.modules.notify.handler.manager import notification_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dianbiao", tags=["电表采集"])

# 采集间隔默认值(秒), 未在配置表下发时的兜底
DEFAULT_INTERVAL_SECONDS = 300

# 采集器代码源目录(搭建触发器时打包上传到目标节点, 打包排除 .env 等敏感/临时文件)
DEFAULT_SOURCE_DIR = os.getenv("DIANBIAO_SOURCE_DIR", "P:/workspace/tools/dianbiao")

# 充值识别: 剩余电量较上一条跳升 > 该值(度) 即判定一次充值; 报文携带 order_value 时按增量判定
CHARGE_DELTA_MIN = float(os.getenv("DIANBIAO_CHARGE_DELTA_MIN", "5"))


# ---------- Token 校验(查库) ----------

def _require_agent_token(x_agent_token: str = Header(..., alias="X-Agent-Token")):
    """采集端令牌校验: 必须存在于 dianbiao_token 且状态为 active"""
    with engine.connect() as conn:
        row = conn.execute(
            dianbiao_token_table.select()
            .where(dianbiao_token_table.c.token == x_agent_token)
        ).fetchone()
    if not row or row.status != "active":
        raise UnauthorizedException(detail="agent token 无效或已作废")
    return x_agent_token


@router.post("/tokens", summary="创建推送 Token")
def create_token(req: schemas.TokenCreate):
    token = secrets.token_urlsafe(24)
    with engine.connect() as conn:
        conn.execute(
            dianbiao_token_table.insert().values(token=token, name=req.name, status="active")
        )
        conn.commit()
    with engine.connect() as conn:
        row = conn.execute(
            dianbiao_token_table.select()
            .where(dianbiao_token_table.c.token == token)
        ).fetchone()
    return BaseResponse.success(_token_to_dict(row))


@router.get("/tokens", summary="推送 Token 列表")
def list_tokens():
    with engine.connect() as conn:
        rows = conn.execute(
            dianbiao_token_table.select()
            .order_by(dianbiao_token_table.c.id.desc())
        ).fetchall()
    return BaseResponse.success([_token_to_dict(r) for r in rows])


@router.post("/tokens/{token_id}/revoke", summary="作废 Token")
def revoke_token(token_id: int):
    with engine.connect() as conn:
        res = conn.execute(
            dianbiao_token_table.update()
            .where(dianbiao_token_table.c.id == token_id,
                   dianbiao_token_table.c.status == "active")
            .values(status="revoked", revoked_at=datetime.now())
        )
        conn.commit()
    if res.rowcount == 0:
        raise NotFoundException(detail="Token 不存在或已作废")
    return BaseResponse.success({"id": token_id, "status": "revoked"})


def _token_to_dict(r):
    return {
        "id": r.id, "token": r.token, "name": r.name, "status": r.status,
        "created_at": r.created_at, "revoked_at": r.revoked_at, "last_used_at": r.last_used_at,
    }


# ---------- 采集器运行配置(mytool 反向下发) ----------

def _config_to_dict(r):
    return {
        "meter_id": r.meter_id,
        "interval_seconds": r.interval_seconds,
        "enabled": r.enabled,
        "updated_at": r.updated_at,
    }


@router.get("/agent/config", summary="采集端拉取运行配置")
def agent_config(meter_id: str = Query(..., description="采集器标识(SN)"),
                 _token: str = Depends(_require_agent_token)):
    with engine.connect() as conn:
        row = conn.execute(
            dianbiao_collector_config_table.select()
            .where(dianbiao_collector_config_table.c.meter_id == meter_id)
        ).fetchone()
    cfg = _config_to_dict(row) if row else {
        "meter_id": meter_id,
        "interval_seconds": DEFAULT_INTERVAL_SECONDS,
        "enabled": 1,
        "updated_at": None,
    }
    return BaseResponse.success(cfg)


@router.get("/collector-configs", summary="采集器配置列表")
def list_collector_configs():
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT m.meter_id, m.name, m.last_seen,
                       c.interval_seconds, c.enabled, c.updated_at
                FROM dianbiao_meter m
                LEFT JOIN dianbiao_collector_config c ON c.meter_id = m.meter_id
                ORDER BY m.last_seen DESC
            """)
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "meter_id": r.meter_id,
            "name": r.name,
            "last_seen": r.last_seen,
            "interval_seconds": r.interval_seconds if r.interval_seconds is not None else DEFAULT_INTERVAL_SECONDS,
            "enabled": r.enabled if r.enabled is not None else 1,
            "configured": r.updated_at is not None,
            "updated_at": r.updated_at,
        })
    return BaseResponse.success(out)


@router.put("/collector-configs", summary="保存采集器配置(反向下发)")
def save_collector_config(req: schemas.CollectorConfigIn):
    _upsert_collector_config(req.meter_id, req.interval_seconds, req.enabled)
    return BaseResponse.success({"meter_id": req.meter_id,
                                 "interval_seconds": req.interval_seconds,
                                 "enabled": req.enabled})


def _upsert_collector_config(meter_id: str, interval_seconds: int, enabled: int):
    """写采集器运行配置(dianbiao_collector_config), 采集端下一轮拉取即生效"""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO dianbiao_collector_config (meter_id, interval_seconds, enabled, updated_at)
                VALUES (:m, :i, :e, :t)
                ON CONFLICT(meter_id) DO UPDATE SET
                    interval_seconds=excluded.interval_seconds,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
            """),
            {"m": meter_id, "i": interval_seconds, "e": enabled, "t": datetime.now()},
        )
        conn.commit()


def _row_to_dict(r):
    return {
        "id": r.id, "meter_id": r.meter_id, "ts": r.ts, "status": r.status,
        "surplus_value": r.surplus_value, "total_value": r.total_value,
        "power": r.power, "voltage": r.voltage, "current": r.current, "pf": r.pf,
        "switch_status": r.switch_status, "order_value": r.order_value,
        "soft_ver": r.soft_ver, "protocol_ver": r.protocol_ver, "tx_msgid": r.tx_msgid,
    }


@router.post("/readings", summary="上报采集数据(幂等)")
def upload_reading(data: schemas.ReadingIn, _token: str = Depends(_require_agent_token)):
    values = {
        "meter_id": data.meter_id, "ts": data.ts, "status": data.status,
        "surplus_value": data.surplus_value, "total_value": data.total_value,
        "power": data.power, "voltage": data.voltage, "current": data.current,
        "pf": data.pf, "switch_status": data.switch_status, "order_value": data.order_value,
        "soft_ver": data.soft_ver, "protocol_ver": data.protocol_ver, "tx_msgid": data.tx_msgid,
        "raw": json.dumps(data.raw, ensure_ascii=False) if data.raw else None,
    }
    # 设备 last_seen 更新 + 首次自动注册
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO dianbiao_meter (meter_id, name, first_seen, last_seen) "
                 "VALUES (:m, :n, :t, :t)"),
            {"m": data.meter_id, "n": data.name, "t": datetime.now()},
        )
        conn.execute(
            text("UPDATE dianbiao_meter SET last_seen=:t, name=COALESCE(:n, name) WHERE meter_id=:m"),
            {"m": data.meter_id, "n": data.name, "t": datetime.now()},
        )
        # 幂等: (meter_id, ts) 唯一, 重复上报忽略
        try:
            res = conn.execute(dianbiao_reading_table.insert().values(**values))
            new_id = res.lastrowid
        except IntegrityError:
            new_id = None  # 已存在(重复上报)
        conn.execute(
            dianbiao_token_table.update()
            .where(dianbiao_token_table.c.token == _token)
            .values(last_used_at=datetime.now())
        )
        conn.commit()
    # 阈值告警评估(不阻塞上报, 命中规则异步推送通知渠道)
    _evaluate_alerts(data)
    # 充值识别(剩余电量跳升/订单金额 → 记一条充值记录, 失败不阻塞上报)
    _detect_charge(data)
    return BaseResponse.success({"id": new_id, "ts": data.ts.isoformat()})


@router.get("/readings", summary="查询读数(时间范围)")
def list_readings(
    meter_id: str = Query(..., description="电表标识"),
    hours: int = Query(24, ge=1, le=720, description="回溯小时数"),
    limit: int = Query(5000, ge=1, le=100000),
):
    since = datetime.now() - timedelta(hours=hours)
    with engine.connect() as conn:
        rows = conn.execute(
            dianbiao_reading_table.select()
            .where(dianbiao_reading_table.c.meter_id == meter_id,
                   dianbiao_reading_table.c.ts >= since)
            .order_by(dianbiao_reading_table.c.ts.desc())
            .limit(limit)
        ).fetchall()
    return BaseResponse.success([_row_to_dict(r) for r in rows])


@router.get("/latest", summary="最新读数")
def latest(meter_id: str = Query(...)):
    with engine.connect() as conn:
        row = conn.execute(
            dianbiao_reading_table.select()
            .where(dianbiao_reading_table.c.meter_id == meter_id)
            .order_by(dianbiao_reading_table.c.ts.desc())
            .limit(1)
        ).fetchone()
    if not row:
        return BaseResponse.success(None)
    return BaseResponse.success(_row_to_dict(row))


@router.get("/meters", summary="电表设备列表")
def list_meters():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT meter_id, name, first_seen, last_seen FROM dianbiao_meter ORDER BY last_seen DESC")
        ).fetchall()
    return BaseResponse.success([dict(r._mapping) for r in rows])


_BUCKET_SQL = {
    "day": "strftime('%Y-%m-%d', ts)",
    "week": "strftime('%Y-W%W', ts)",
    "month": "strftime('%Y-%m', ts)",
    "quarter": "strftime('%Y', ts) || '-Q' || ((CAST(strftime('%m', ts) AS INTEGER) + 2) / 3)",
    "year": "strftime('%Y', ts)",
}
_BUCKET_DAYS = {"day": 30, "week": 90, "month": 365, "quarter": 730, "year": 1825}
_BUCKET_LABELS = {
    "day": "日", "week": "周", "month": "月", "quarter": "季", "year": "年",
}


@router.get("/stats", summary="按日/周/月/季/年聚合统计")
def stats(
    meter_id: str = Query(...),
    bucket: str = Query("day", description="聚合粒度: day/week/month/quarter/year"),
    days: int = Query(None, ge=1, le=3650, description="回溯天数(默认按粒度取合理值)"),
    start: str = Query(None, description="起始日期(YYYY-MM-DD), 与 days 二选一, 窗口=[start 当日, 现在]"),
):
    if bucket not in _BUCKET_SQL:
        raise NotFoundException(detail=f"不支持的聚合粒度: {bucket}")
    if start:
        try:
            since = datetime.strptime(start, "%Y-%m-%d")
        except ValueError:
            raise NotFoundException(detail=f"start 格式应为 YYYY-MM-DD, 收到: {start}")
    else:
        since = datetime.now() - timedelta(days=days or _BUCKET_DAYS[bucket])
    sql = text(f"""
        SELECT {_BUCKET_SQL[bucket]} AS bucket,
               MAX(total_value) AS total_max,
               MIN(total_value) AS total_min,
               AVG(power) AS power_avg,
               COUNT(*) AS cnt
        FROM dianbiao_reading
        WHERE meter_id = :m AND ts >= :since
        GROUP BY bucket
        ORDER BY bucket
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"m": meter_id, "since": since}).fetchall()
    out = []
    for r in rows:
        usage = None
        if r.total_max is not None and r.total_min is not None and r.total_max > r.total_min:
            usage = round(r.total_max - r.total_min, 2)
        out.append({
            "bucket": r.bucket,
            "usage": usage,                        # 区间用电增量(度), 由 total 差分
            "power_avg": round(float(r.power_avg), 2) if r.power_avg is not None else None,
            "readings": r.cnt,
        })
    return BaseResponse.success({"meter_id": meter_id, "bucket": bucket, "days": out})


# ============================================================
# 采集器部署触发器(节点 + 目录位置 + 初始化 doctor + 反推配置)
# ============================================================

_LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


def _is_local_host(node) -> bool:
    """本机节点(直接 subprocess 执行, 不依赖本机 sshd)"""
    host = node["host"] if isinstance(node, dict) else node.host
    return host in _LOCAL_HOSTS


def _run_on_node(node, work_dir: str, command: str, timeout: int = 60):
    """在节点 work_dir 下执行命令。本机 subprocess, 远程走 SSH。

    Returns:
        (exit_code, output)  exit_code=0 表示成功; output 为 stdout+stderr 合并
    """
    if _is_local_host(node):
        try:
            proc = subprocess.run(
                command, cwd=work_dir, shell=True,
                capture_output=True, text=True, timeout=timeout,
            )
            return proc.returncode, (proc.stdout or "").strip() + "\n" + (proc.stderr or "").strip()
        except Exception as e:
            return 1, f"本地执行失败: {e}"
    ssh = SSHClient(NodeRead(
        id=node["id"], name=node["name"], host=node["host"], port=node["port"],
        username=node["username"], auth_type=node["auth_type"],
        password=node["password"], private_key=node.get("private_key"), is_active=True,
    ))
    connected = False
    try:
        ssh.connect()
        connected = True
        exit_code, out, err = ssh.execute_command(f"cd {work_dir} && {command}", timeout=timeout)
        return exit_code, ((out or "") + (err or "")).strip()
    except Exception as e:
        return 1, f"SSH 执行失败: {e}"
    finally:
        if connected:
            ssh.close()


def _read_env_sn(node, work_dir: str) -> str:
    """读取节点上采集器 .env 的 YM_SN(采集器 meter_id)"""
    return _read_env_var(node, work_dir, "YM_SN")


def _read_env_var(node, work_dir: str, key: str) -> str:
    """读节点上采集器 .env 中指定 KEY 的值(不存在返回空串)"""
    try:
        if _is_local_host(node):
            env_path = os.path.join(work_dir, ".env")
            if not os.path.exists(env_path):
                return ""
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip()
            return ""
        code, out = _run_on_node(node, work_dir, f"grep -E '^{key}=' .env | head -1", timeout=20)
        if code != 0:
            return ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
        return ""
    except Exception:
        return ""


def _merge_env_kvs(content: str, kvs: dict) -> str:
    """在 .env 文本里替换/追加 KV(保留注释与未知键); 值非空的键才会写"""
    lines = content.splitlines()
    pending = {k: v for k, v in kvs.items() if v}
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in pending:
                out.append(f"{k}={pending.pop(k)}")
                continue
        out.append(line)
    for k, v in pending.items():
        out.append(f"{k}={v}")
    return "\n".join(out)


def _write_env_kvs(node, work_dir: str, kvs: dict):
    """把 KV 写入节点采集器的 .env(先备份 .env.bak; 保持其它配置不动)"""
    if not kvs:
        return
    if _is_local_host(node):
        env_path = os.path.join(work_dir, ".env")
        content = ""
        if os.path.exists(env_path):
            shutil.copy(env_path, env_path + ".bak")
            with open(env_path, encoding="utf-8") as f:
                content = f.read()
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(_merge_env_kvs(content, kvs))
        return
    ssh = SSHClient(NodeRead(
        id=node["id"], name=node["name"], host=node["host"], port=node["port"],
        username=node["username"], auth_type=node["auth_type"],
        password=node["password"], private_key=node.get("private_key"), is_active=True,
    ))
    connected = False
    try:
        ssh.connect()
        connected = True
        env_path = f"{work_dir}/.env"
        content = ""
        if ssh.exists(env_path):
            ssh.execute_command(f"cp {env_path} {env_path}.bak", timeout=20)
            content = ssh.download_fileobj(env_path).read().decode("utf-8", errors="replace")
        merged = _merge_env_kvs(content, kvs)
        ssh.upload_fileobj(io.BytesIO(merged.encode("utf-8")), env_path)
    finally:
        if connected:
            ssh.close()


def _create_agent_token(name: str) -> str:
    """创建新的上报 token(写入 dianbiao_token 表)"""
    token = secrets.token_urlsafe(24)
    with engine.begin() as conn:
        conn.execute(
            dianbiao_token_table.insert().values(token=token, name=name, status="active")
        )
    return token


def _agent_token_valid(token: str) -> bool:
    """Token 必须存在于 dianbiao_token 表且状态 active 才算有效"""
    if not token:
        return False
    with engine.connect() as conn:
        row = conn.execute(
            dianbiao_token_table.select().where(dianbiao_token_table.c.token == token)
        ).fetchone()
    return bool(row and row.status == "active")


# ---------- 代码分发(打包 source_dir → SFTP 部署到节点, 不含 .env) ----------

_SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", "logs", "backup", "backups", "dist", ".pytest_cache"}


def _make_source_zip(source_dir: str) -> str:
    """把采集器代码源目录打成临时 zip(排除 .env/.git/__pycache__/备份数据/日志)"""
    src = Path(source_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"代码源目录不存在: {source_dir}")
    fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(src.rglob("*")):
                if f.is_dir():
                    continue
                rel = f.relative_to(src).as_posix()
                parts = rel.split("/")
                if any(p in _SKIP_DIRS for p in parts):
                    continue
                if f.name.startswith(".env"):
                    continue  # 敏感配置绝不进包(.env / .env.local 等)
                if f.name.endswith((".jsonl", ".log", ".pyc")):
                    continue
                zf.write(f, rel)
        return zip_path
    except Exception:
        os.remove(zip_path)
        raise


def _deploy_zip(node, work_dir: str, zip_path: str):
    """把代码包部署到节点 work_dir(本机直接解压, 远程 SFTP 上传后 unzip)"""
    if _is_local_host(node):
        os.makedirs(work_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            for m in zf.infolist():
                target = os.path.join(work_dir, m.filename)
                if m.is_dir():
                    os.makedirs(target, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(m) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        return
    ssh = SSHClient(NodeRead(
        id=node["id"], name=node["name"], host=node["host"], port=node["port"],
        username=node["username"], auth_type=node["auth_type"],
        password=node["password"], private_key=node.get("private_key"), is_active=True,
    ))
    connected = False
    try:
        ssh.connect()
        connected = True
        remote_zip = f"/tmp/dianbiao_src_{int(time.time() * 1000)}.zip"
        ssh.upload_file(zip_path, remote_zip)
        exit_code, out, err = ssh.execute_command(
            f"mkdir -p {work_dir} && (unzip -o {remote_zip} -d {work_dir} 2>/dev/null "
            f"|| python3 -m zipfile -e {remote_zip} {work_dir}) && rm -f {remote_zip}",
            timeout=120,
        )
        if exit_code != 0:
            raise Exception(f"解压失败: {(out or '') + (err or '')}".strip())
    finally:
        if connected:
            ssh.close()


def _sync_source_to_node(node, work_dir: str, source_dir: str) -> str:
    """把代码源目录同步(打包+上传+解压)到节点 work_dir, 返回部署摘要"""
    zip_path = _make_source_zip(source_dir)
    try:
        _deploy_zip(node, work_dir, zip_path)
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass
    return f"代码包已同步: {source_dir} → 节点:{work_dir} (不含 .env)"


def _default_mytool_url() -> str:
    """推断 mytool 后端地址(供节点采集器上报), 优先级: 环境变量 > 本机局域网 IP + 8000"""
    env_url = os.getenv("MYTOOL_PUBLIC_URL", "").strip()
    if env_url:
        return env_url
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        try:
            s.connect(("8.8.8.8", 80))  # 取默认出口网卡 IP
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
    except Exception:
        ip = "127.0.0.1"
    return f"http://{ip}:8000"


def _ensure_collector_process(node, work_dir: str, want_start: bool) -> str:
    """按开关状态在节点上拉起/停止采集器常驻进程(collector.py)。

    用 pidfile 判断是否已在运行(bash -c 自身命令行会匹配 pgrep -f, 不可靠);
    返回一行过程描述。
    """
    pid_file = os.path.join(work_dir, "collector.pid") if _is_local_host(node) else f"{work_dir}/collector.pid"
    if want_start:
        code, out = _run_on_node(
            node, work_dir,
            f"{'python' if _is_local_host(node) else 'python3'} -c 'import os, sys; print(sys.version.split()[0])' > /dev/null 2>&1",
            timeout=30,
        )
        if code != 0:
            return "未找到 Python 解释器, 请安装 Python 3"
        # Spark 启动: 已运行则跳过; 否则后台拉起并写 pidfile
        code, out = _run_on_node(
            node, work_dir,
            f"if [ -f {pid_file} ] && kill -0 $(cat {pid_file}) 2>/dev/null; then "
            f"echo COLLECTOR_ALREADY:$(cat {pid_file}); "
            f"else (nohup {'python3' if not _is_local_host(node) else 'python'} collector.py >> collector.log 2>&1 < /dev/null & echo $! > {pid_file}); "
            f"sleep 1; "
            f"if kill -0 $(cat {pid_file}) 2>/dev/null; then "
            f"echo COLLECTOR_STARTED:$(cat {pid_file}); "
            f"else echo '启动采集器失败, 请查看 collector.log'; fi; fi",
            timeout=60,
        )
        out = (out or "").strip()
        if out.startswith("COLLECTOR_STARTED:"):
            return f"采集器已启动(pid {out.split(':')[1]}, 日志 collector.log)"
        if out.startswith("COLLECTOR_ALREADY:"):
            return f"采集器已在运行(pid {out.split(':')[1]}), 跳过启动"
        return out or "启动采集器: 无输出"
    # 停采: 终止常驻进程(pidfile 优先, 兜底 pkill 防止 pid 文件丢失)
    code, out = _run_on_node(
        node, work_dir,
        f"[ -f {pid_file} ] && kill $(cat {pid_file}) 2>/dev/null; "
        f"pkill -f '[c]ollector.py' 2>/dev/null; rm -f {pid_file}; echo done",
        timeout=30,
    )
    return "已停止采集进程" if code == 0 else f"停止采集进程失败: {out}"


def _trigger_to_dict(r):
    return {
        "id": r.id, "name": r.name, "node_id": r.node_id, "node_name": r.node_name,
        "node_host": r.node_host, "work_dir": r.work_dir, "source_dir": r.source_dir,
        "meter_id": r.meter_id, "ym_mac": r.ym_mac, "agent_token": r.agent_token,
        "mytool_url": r.mytool_url,
        "interval_seconds": r.interval_seconds, "enabled": r.enabled,
        "init_status": r.init_status, "init_output": r.init_output, "init_at": r.init_at,
        "created_at": r.created_at, "updated_at": r.updated_at,
    }


@router.get("/triggers", summary="采集器触发器列表")
def list_triggers():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT t.*, n.name AS node_name
            FROM dianbiao_trigger t
            LEFT JOIN nodes n ON n.id = t.node_id
            ORDER BY t.id DESC
        """)).fetchall()
    return BaseResponse.success([_trigger_to_dict(r) for r in rows])


@router.post("/triggers", summary="搭建采集器触发器(所属节点+目录)")
def create_trigger(req: schemas.TriggerCreate):
    node = _get_node_or_404(req.node_id)
    with engine.connect() as conn:
        res = conn.execute(
            dianbiao_trigger_table.insert().values(
                name=req.name or f"{node['name']} 采集触发器",
                node_id=req.node_id,
                node_host=f"{node['host']}:{node['port']}",
                work_dir=req.work_dir,
                source_dir=req.source_dir or DEFAULT_SOURCE_DIR,
                meter_id=req.meter_id or None,
                ym_mac=req.ym_mac or None,
                agent_token=req.agent_token or None,
                mytool_url=req.mytool_url or None,
                interval_seconds=req.interval_seconds,
                enabled=req.enabled,
                init_status="pending",
            )
        )
        conn.commit()
        new_id = res.lastrowid
    return BaseResponse.success({"id": new_id})


@router.post("/triggers/{trigger_id}/init", summary="初始化触发器(代码同步 + 配置下发 + 远端 doctor)")
def init_trigger(trigger_id: int):
    row = _get_trigger_or_404(trigger_id)
    node = _get_node_or_404(row["node_id"])
    steps = []
    # 1) 代码分发: 打包 source_dir(SFTP/本机)部署到节点, 不含 .env
    if row.get("source_dir"):
        try:
            steps.append(_sync_source_to_node(node, row["work_dir"], row["source_dir"]))
        except Exception as e:
            steps.append(f"⚠ 代码同步失败(继续尝试远端 doctor): {e}")
    else:
        steps.append("未配置代码源目录(应用节点已有代码)")
    # 2) 环境变量下发: SN / MAC / 上报 Token 写入节点 .env(不存在则自动创建 Token)
    kvs = {}
    if row.get("meter_id"):
        kvs["YM_SN"] = row["meter_id"]
    if row.get("ym_mac"):
        kvs["YM_MAC"] = row["ym_mac"]
    agent_token = row.get("agent_token")
    # 触发器配了 token 但无效(不存在/已作废) → 自动换新, 保证下发的 Token 一定可用
    if agent_token and not _agent_token_valid(agent_token):
        steps.append(f"⚠ 配置的 Token 无效(已作废/不存在), 自动创建新 Token 替换")
        agent_token = None
    if not agent_token:
        existing = _read_env_var(node, row["work_dir"], "MYTOOL_AGENT_TOKEN")
        if existing and _agent_token_valid(existing):
            agent_token = existing
            steps.append("复用节点 .env 已有有效 MYTOOL_AGENT_TOKEN")
        else:
            agent_token = _create_agent_token((row.get("name") or "采集触发器") + "-自动")
            with engine.begin() as conn:
                conn.execute(
                    dianbiao_trigger_table.update()
                    .where(dianbiao_trigger_table.c.id == trigger_id)
                    .values(agent_token=agent_token)
                )
            steps.append("[token] 已自动创建上报 Token(active)并写入节点 .env")
    if agent_token:
        kvs["MYTOOL_AGENT_TOKEN"] = agent_token
    # mytool 后端地址: 触发器自定义优先, 否则自动推断(环境变量/本机 IP+8000)
    mytool_url = (row.get("mytool_url") or "").strip() or _default_mytool_url()
    if mytool_url:
        kvs["MYTOOL_URL"] = mytool_url
    if kvs:
        try:
            _write_env_kvs(node, row["work_dir"], kvs)
            steps.append("[env] .env 已下发 " + ", ".join(kvs.keys()))
        except Exception as e:
            steps.append(f"⚠ .env 下发失败: {e}")
    # 3) 远端环境自检
    code, output = _run_on_node(
        node, row["work_dir"],
        "python meter_read.py --doctor || python3 meter_read.py --doctor",
        timeout=120,
    )
    # 4) doctor 校验通过 → 反推基线配置 + 按"运行开关"自动拉起/停止采集进程
    meter_id = ""
    if code == 0:
        meter_id = _read_env_sn(node, row["work_dir"])
    init_status = "ok" if code == 0 else "fail"
    if code == 0 and meter_id:
        _upsert_collector_config(meter_id, row["interval_seconds"], row["enabled"])
    if code == 0:
        try:
            run_msg = _ensure_collector_process(
                node, row["work_dir"], want_start=(row.get("enabled") == 1))
            steps.append(run_msg)
        except Exception as e:
            steps.append(f"⚠ 自动{'启动' if row.get('enabled') == 1 else '停止'}采集失败: {e}")
    else:
        steps.append("⚠ doctor 未通过, 跳过启动采集进程")
    full_output = ("\n".join(steps) + "\n" + output.strip()).strip()[-4000:]
    with engine.connect() as conn:
        conn.execute(
            dianbiao_trigger_table.update()
            .where(dianbiao_trigger_table.c.id == trigger_id)
            .values(
                init_status=init_status,
                init_output=full_output or None,
                init_at=datetime.now(),
                meter_id=meter_id or row["meter_id"] or None,
            )
        )
        conn.commit()
    return BaseResponse.success({
        "id": trigger_id, "init_status": init_status,
        "meter_id": meter_id or row["meter_id"] or None,
        "agent_token": agent_token or None,
        "output": full_output,
    })


@router.put("/triggers/{trigger_id}", summary="更新触发器并反推配置到采集器")
def update_trigger(trigger_id: int, req: schemas.TriggerUpdate):
    row = _get_trigger_or_404(trigger_id)
    values = {}
    if req.name is not None:
        values["name"] = req.name
    if req.work_dir is not None:
        values["work_dir"] = req.work_dir
    if req.source_dir is not None:
        values["source_dir"] = req.source_dir or DEFAULT_SOURCE_DIR
    if req.meter_id is not None:
        values["meter_id"] = req.meter_id or None
    if req.ym_mac is not None:
        values["ym_mac"] = req.ym_mac or None
    if req.agent_token is not None:
        values["agent_token"] = req.agent_token or None
    if req.mytool_url is not None:
        values["mytool_url"] = req.mytool_url or None
    if req.interval_seconds is not None:
        values["interval_seconds"] = req.interval_seconds
    if req.enabled is not None:
        values["enabled"] = req.enabled
    if not values:
        raise NotFoundException(detail="没有需要更新的字段")

    with engine.connect() as conn:
        conn.execute(
            dianbiao_trigger_table.update()
            .where(dianbiao_trigger_table.c.id == trigger_id)
            .values(**values)
        )
        conn.commit()
    # 已绑定采集器 → 启停/间隔同步反推; SN 变更时按新 SN 反推
    meter_id = values.get("meter_id", row["meter_id"])
    pushed = False
    if meter_id:
        _upsert_collector_config(
            meter_id,
            values.get("interval_seconds", row["interval_seconds"]),
            values.get("enabled", row["enabled"]),
        )
        pushed = True
    # 启停开关变更 → 同步节点上常驻采集进程
    proc = ""
    new_enabled = values.get("enabled", row["enabled"])
    if meter_id and "enabled" in values:
        try:
            node = _get_node_or_404(row["node_id"])
            proc = _ensure_collector_process(
                node, row["work_dir"], want_start=(new_enabled == 1))
        except Exception as e:
            proc = f"同步进程失败: {e}"
    return BaseResponse.success({"id": trigger_id, "pushed": pushed, "proc": proc, **values})


@router.delete("/triggers/{trigger_id}", summary="删除采集器触发器")
def delete_trigger(trigger_id: int):
    with engine.connect() as conn:
        res = conn.execute(
            text("DELETE FROM dianbiao_trigger WHERE id = :id"), {"id": trigger_id}
        )
        conn.commit()
    if res.rowcount == 0:
        raise NotFoundException(detail=f"触发器 {trigger_id} 不存在")
    return BaseResponse.success({"id": trigger_id})


def _get_trigger_or_404(trigger_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM dianbiao_trigger WHERE id = :id"), {"id": trigger_id}
        ).fetchone()
    if not row:
        raise NotFoundException(detail=f"触发器 {trigger_id} 不存在")
    return dict(row._mapping)


def _get_node_or_404(node_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM nodes WHERE id = :id"), {"id": node_id}
        ).fetchone()
    if not row:
        raise NotFoundException(detail=f"节点 {node_id} 不存在")
    return dict(row._mapping)


# ============================================================
# 充值识别(上报时自动记录: 剩余电量跳升 或 报文携带 order_value)
# ============================================================

def _detect_charge(data: schemas.ReadingIn):
    """对比上一条读数识别充值事件, 写入 dianbiao_charge。

    - surplus_value 环比上涨且涨幅 > CHARGE_DELTA_MIN → 充值(jump, 以度记录)
    - 报文 order_value 相对上一条上涨 → 充值(order, 以报文增量记录)
    - order_value 通常为累计/档案值(如 192.31 恒定), 首次出现只作基线不算事件,
      否则每条上报都会误记一条充值
    - 同一 (meter_id, ts) 幂等, 失败仅记日志, 不阻塞上报
    """
    try:
        if data.surplus_value is None:
            return
        with engine.connect() as conn:
            prev = conn.execute(
                text("SELECT surplus_value, order_value FROM dianbiao_reading "
                     "WHERE meter_id=:m AND ts < :ts ORDER BY ts DESC LIMIT 1"),
                {"m": data.meter_id, "ts": data.ts},
            ).fetchone()
            if not prev or prev.surplus_value is None:
                return
            jump = round(float(data.surplus_value) - float(prev.surplus_value), 4)
            if jump > CHARGE_DELTA_MIN:
                conn.execute(
                    dianbiao_charge_table.insert().values(
                        meter_id=data.meter_id, ts=data.ts,
                        prev_value=prev.surplus_value, new_value=data.surplus_value,
                        delta=jump, order_value=data.order_value, mode="jump",
                    )
                )
                conn.commit()
                return
            if prev.order_value is not None and data.order_value is not None:
                order_inc = round(float(data.order_value) - float(prev.order_value), 4)
                if order_inc > 0:
                    conn.execute(
                        dianbiao_charge_table.insert().values(
                            meter_id=data.meter_id, ts=data.ts,
                            prev_value=prev.order_value, new_value=data.order_value,
                            delta=order_inc, order_value=data.order_value, mode="order",
                        )
                    )
                    conn.commit()
    except Exception as e:
        logger.warning(f"充值识别失败: {e}")


@router.get("/charges", summary="充值记录(上报时自动识别)")
def list_charges(meter_id: str = Query(None, description="电表标识, 缺省返回全部"),
                 limit: int = Query(50, ge=1, le=500, description="条数(按时间倒序)")):
    with engine.connect() as conn:
        stmt = text("""
            SELECT c.*, m.name AS meter_name
            FROM dianbiao_charge c
            LEFT JOIN dianbiao_meter m ON m.meter_id = c.meter_id
            WHERE (:mid IS NULL OR c.meter_id = :mid)
            ORDER BY c.ts DESC, c.id DESC
            LIMIT :lim
        """)
        rows = conn.execute(stmt, {"mid": meter_id, "lim": limit}).fetchall()
    out = [dict(r._mapping) for r in rows]
    for d in out:
        d["mode_label"] = "订单" if d["mode"] == "order" else (f"剩余+{d['delta']:g}" if d["delta"] else "")
        d["amount_label"] = f"+{d['delta']:g}" if d["delta"] is not None else ""
    return BaseResponse.success(out)


# ============================================================
# 阈值告警(读数上报时评估, 命中后经「通知渠道」页配置的渠道推送)
# ============================================================

_ALERT_METRICS = {
    "surplus_value": "剩余电量",
    "total_value": "累计用电",
    "power": "功率",
    "voltage": "电压",
    "current": "电流",
}
_ALERT_CONDITIONS = {"lt": "低于", "gt": "高于"}
_ALERT_METRIC_UNITS = {
    "surplus_value": "度", "total_value": "度", "power": "W", "voltage": "V", "current": "A",
}


@router.get("/notify-services", summary="可用的通知渠道(已启用, 供告警规则下拉)")
def list_enabled_notify_services():
    with engine.connect() as conn:
        rows = conn.execute(
            notification_services_table.select()
            .where(notification_services_table.c.is_enabled == True)  # noqa: E712
            .order_by(notification_services_table.c.id)
        ).fetchall()
    return BaseResponse.success([
        {"id": r.id, "service_name": r.service_name, "service_type": r.service_type}
        for r in rows
    ])


@router.get("/alerts", summary="阈值告警规则列表")
def list_alerts(meter_id: str = Query(None, description="电表标识, 缺省返回全部")):
    with engine.connect() as conn:
        stmt = select(dianbiao_alert_table)
        if meter_id:
            stmt = stmt.where(dianbiao_alert_table.c.meter_id == meter_id)
        rows = conn.execute(stmt.order_by(dianbiao_alert_table.c.id)).fetchall()
        meter_names = {
            r.meter_id: r.name
            for r in conn.execute(text("SELECT meter_id, name FROM dianbiao_meter")).fetchall()
        }
        svc_names = {
            r.id: r.service_name
            for r in conn.execute(text("SELECT id, service_name FROM notification_services")).fetchall()
        }
    out = []
    for r in rows:
        d = dict(r._mapping)
        d["meter_name"] = meter_names.get(d["meter_id"])
        d["service_name"] = svc_names.get(d["service_id"])
        d["metric_label"] = _ALERT_METRICS.get(d["metric"], d["metric"])
        d["condition_label"] = _ALERT_CONDITIONS.get(d["condition"], d["condition"])
        d["unit"] = _ALERT_METRIC_UNITS.get(d["metric"], "")
        out.append(d)
    return BaseResponse.success(out)


@router.post("/thresholds", summary="新增阈值告警规则")
def create_alert(req: schemas.AlertCreate):
    if req.metric not in _ALERT_METRICS:
        raise NotFoundException(detail=f"不支持的指标: {req.metric}, 可选: {', '.join(_ALERT_METRICS)}")
    if req.condition not in _ALERT_CONDITIONS:
        raise NotFoundException(detail=f"不支持的比较条件: {req.condition}")
    with engine.connect() as conn:
        row = conn.execute(
            select(notification_services_table.c.id)
            .where(notification_services_table.c.id == req.service_id,
                   notification_services_table.c.is_enabled == True)  # noqa: E712
        ).fetchone()
        if not row:
            raise NotFoundException(detail=f"通知渠道 {req.service_id} 不存在或未启用, 请先在「通知渠道」页启用")
        res = conn.execute(
            dianbiao_alert_table.insert().values(
                meter_id=req.meter_id, metric=req.metric, condition=req.condition,
                threshold=req.threshold, service_id=req.service_id,
                cooldown_minutes=req.cooldown_minutes, enabled=req.enabled,
            )
        )
        new_id = res.lastrowid
        conn.commit()
    return BaseResponse.success({"id": new_id})


@router.put("/thresholds/{alert_id}", summary="更新阈值告警规则")
def update_alert(alert_id: int, req: schemas.AlertUpdate):
    values = {}
    for f in ("meter_id", "metric", "condition", "threshold", "service_id",
              "cooldown_minutes", "enabled"):
        v = getattr(req, f)
        if v is not None:
            values[f] = v
    if "metric" in values and values["metric"] not in _ALERT_METRICS:
        raise NotFoundException(detail=f"不支持的指标: {values['metric']}")
    if "condition" in values and values["condition"] not in _ALERT_CONDITIONS:
        raise NotFoundException(detail=f"不支持的比较条件: {values['condition']}")
    with engine.connect() as conn:
        row = conn.execute(
            select(dianbiao_alert_table.c.id)
            .where(dianbiao_alert_table.c.id == alert_id)
        ).fetchone()
        if not row:
            raise NotFoundException(detail=f"阈值规则 {alert_id} 不存在")
        if "service_id" in values:
            svc = conn.execute(
                select(notification_services_table.c.id)
                .where(notification_services_table.c.id == values["service_id"],
                       notification_services_table.c.is_enabled == True)  # noqa: E712
            ).fetchone()
            if not svc:
                raise NotFoundException(detail=f"通知渠道 {values['service_id']} 不存在或未启用")
        values["updated_at"] = datetime.now()
        conn.execute(
            dianbiao_alert_table.update()
            .where(dianbiao_alert_table.c.id == alert_id)
            .values(**values)
        )
        conn.commit()
    return BaseResponse.success({"id": alert_id})


@router.delete("/thresholds/{alert_id}", summary="删除阈值告警规则")
def delete_alert(alert_id: int):
    with engine.connect() as conn:
        res = conn.execute(
            dianbiao_alert_table.delete().where(dianbiao_alert_table.c.id == alert_id)
        )
        conn.commit()
    if res.rowcount == 0:
        raise NotFoundException(detail=f"阈值规则 {alert_id} 不存在")
    return BaseResponse.success({"id": alert_id})


def _evaluate_alerts(data: schemas.ReadingIn):
    """每收到一条上报采样, 检查该电表的启用规则; 命中且冷却已过则异步推送通知。

    通知发送在守护线程内用独立事件循环执行, 不阻塞采集端上报。
    """
    try:
        rows = None
        with engine.connect() as conn:
            rows = conn.execute(
                select(dianbiao_alert_table)
                .where(dianbiao_alert_table.c.meter_id == data.meter_id,
                       dianbiao_alert_table.c.enabled == 1)
            ).fetchall()
        if not rows:
            return
        for r in rows:
            value = getattr(data, r.metric, None)
            if value is None:
                continue
            hit = value < r.threshold if r.condition == "lt" else value > r.threshold
            if not hit:
                continue
            now = datetime.now()
            if r.last_alert_at is not None:
                wait_minutes = (now - r.last_alert_at).total_seconds() / 60
                if wait_minutes < (r.cooldown_minutes or 10):
                    continue
            # 更新最近告警时间/值(先占位, 防并发重复触发)
            with engine.begin() as conn:
                conn.execute(
                    dianbiao_alert_table.update()
                    .where(dianbiao_alert_table.c.id == r.id)
                    .values(last_alert_at=now, last_value=value)
                )
            threading.Thread(
                target=_fire_alert,
                args=(r.id, data.meter_id, r.metric, r.condition, r.threshold,
                      r.service_id, value, data.name),
                daemon=True,
            ).start()
    except Exception as e:
        logger.warning("阈值告警评估异常: %s", e)


def _fire_alert(alert_id, meter_id, metric, condition, threshold,
                service_id, value, meter_name):
    """后台线程: 通过通知渠道发送告警(发送失败仅记日志, 不影响采集)"""
    import asyncio

    metric_label = _ALERT_METRICS.get(metric, metric)
    cond_label = _ALERT_CONDITIONS.get(condition, condition)
    unit = _ALERT_METRIC_UNITS.get(metric, "")
    show = f"{meter_name or meter_id}"
    title = f"电表告警: {metric_label}{cond_label}阈值"
    content = (
        f"电表「{show}」{metric_label}当前值 {value}{unit}, "
        f"{cond_label}阈值 {threshold}{unit}。\n"
        f"(规则 #{alert_id}, 请及时检查)"
    )

    async def _send():
        try:
            results = await notification_manager.send_notification(
                title=title, content=content, service_id=service_id,
            )
            ok = all(r.get("success") for r in results)
            logger.info("阈值告警已推送[%s] 规则#%s -> %s: %s", meter_id, alert_id,
                        (results or [{}])[0].get("service_name", service_id),
                        "成功" if ok else "失败")
            if not ok:
                logger.warning("阈值告警推送失败: %s", results)
        except Exception as e:
            logger.error("阈值告警发送异常(规则 %s): %s", alert_id, e)

    asyncio.run(_send())