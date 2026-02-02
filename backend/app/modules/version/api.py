import logging
from pathlib import Path

from fastapi import APIRouter
import sys
import httpx
import asyncio
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/version", tags=["version"])

# ===== 单一缓存 =====
CACHE_TTL = 300  # 5 分钟
_cache = {
    "latest_version": None,      # 必缓存
    "updated_at": None,         # 可选缓存
    "fetched_at": None,         # 版本获取时间
}
_cache_lock = asyncio.Lock()

# ===== 配置 =====
REPO_USER = "upchr"
REPO_NAME = "FnDepot"
BRANCH = "main"
VERSION_URL=f"https://gitee.com/{REPO_USER}/{REPO_NAME}/raw/{BRANCH}/fnpack.json"

def get_current_version():
    try:
        if sys.platform.startswith("win"):
            version_dir = Path.cwd().parent
        else:
            version_dir=Path("/toolsplus")
        version_file = f"{version_dir}/version.txt"
        logger.info(f"version版本文件路径：{version_file}")

        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

# ===== 获取最新版本（核心）=====
async def _fetch_latest_version():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(VERSION_URL, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                last_version=f"v{data['toolsplus']['version']}"
                last_time=data['toolsplus']['lasttime']
                return last_version,last_time
        except Exception:
            return None,None
    return None,None



@router.get("/")
async def get_version():
    now = datetime.now()
    current = get_current_version()

    async with _cache_lock:
        # 检查版本缓存是否有效
        if (
                _cache["latest_version"] is not None and
                _cache["updated_at"] is not None and
                (now - _cache["fetched_at"]) < timedelta(seconds=CACHE_TTL)
        ):
            latest = _cache["latest_version"]
            lasttime = _cache["updated_at"]
        else:
            # 重新获取版本
            latest,lasttime = await _fetch_latest_version()
            _cache["latest_version"] = latest
            _cache["updated_at"] = lasttime
            _cache["fetched_at"] = now
            # 注意：不清除 updated_at 缓存

    updatable = latest is not None and latest != "unknown" and latest != current
    return {
        "current": current,
        "latest": latest,
        "updatable": updatable,
        "updated_at": lasttime  # 明确不返回
    }
