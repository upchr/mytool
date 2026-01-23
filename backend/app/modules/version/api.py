from fastapi import APIRouter
import os
import sys
import httpx
import asyncio
from datetime import datetime, timedelta

router = APIRouter(prefix="/version", tags=["version"])

# ===== 单一缓存 =====
CACHE_TTL = 300  # 5 分钟
_cache = {
    "latest_version": None,      # 必缓存
    "updated_at": None,         # 可选缓存
    "fetched_at": None,         # 版本获取时间
    "time_fetched_at": None     # 时间获取时间
}
_cache_lock = asyncio.Lock()

# ===== 配置 =====
REPO_USER = "upchr"
REPO_NAME = "FnDepot"
BRANCH = "main"

PROXIES = [
    {"name": "jsdelivr",    "type": "cdn",     "base": f"https://cdn.jsdelivr.net/gh/{REPO_USER}/{REPO_NAME}@{BRANCH}/"},
    {"name": "gh-proxy",    "type": "proxy",   "base": "https://gh-proxy.org/https://"},
    {"name": "hk-gh-proxy", "type": "proxy",   "base": "https://hk.gh-proxy.org/https://"},
    {"name": "cdn-gh-proxy","type": "proxy",   "base": "https://cdn.gh-proxy.org/https://"},
    {"name": "direct",      "type": "raw",     "base": "https://"},
]

def build_github_url(path: str, is_api: bool = False) -> list[str]:
    urls = []
    for proxy in PROXIES:
        if is_api:
            if proxy["type"] == "proxy":
                url = proxy["base"] + "api.github.com/" + path
            elif proxy["name"] == "direct":
                url = proxy["base"] + "api.github.com/" + path
            else:
                continue
        else:
            if proxy["type"] == "cdn":
                url = proxy["base"] + path
            else:
                raw_path = f"raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/{BRANCH}/{path}"
                url = proxy["base"] + raw_path
        urls.append(url)
    return urls

def get_current_version():
    try:
        if sys.platform.startswith("win"):
            base = os.path.abspath("./data")
            version_file = os.path.join(base, "version.txt")
        else:
            version_file = "/app/version.txt"
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

# ===== 获取最新版本（核心）=====
async def _fetch_latest_version():
    async with httpx.AsyncClient() as client:
        fnpack_urls = build_github_url("fnpack.json")
        for url in fnpack_urls:
            try:
                resp = await client.get(url, timeout=6.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return f"v{data['toolsplus']['version']}"
            except Exception:
                continue
    return None

# ===== 获取更新时间（按需）=====
async def _fetch_updated_at():
    async with httpx.AsyncClient() as client:
        api_path = f"repos/{REPO_USER}/{REPO_NAME}/commits?path=fnpack.json&per_page=1"
        commit_urls = build_github_url(api_path, is_api=True)
        for url in commit_urls:
            try:
                resp = await client.get(url, timeout=6.0)
                if resp.status_code == 200:
                    commits = resp.json()
                    if commits:
                        return commits[0]["commit"]["author"]["date"]
            except Exception:
                continue
    return None

# ===== 接口1：/version/ （只用版本缓存）=====
@router.get("/")
async def get_version():
    now = datetime.now()
    current = get_current_version()

    async with _cache_lock:
        # 检查版本缓存是否有效
        if (
                _cache["latest_version"] is not None and
                _cache["fetched_at"] is not None and
                (now - _cache["fetched_at"]) < timedelta(seconds=CACHE_TTL)
        ):
            latest = _cache["latest_version"]
        else:
            # 重新获取版本
            latest = await _fetch_latest_version()
            _cache["latest_version"] = latest
            _cache["fetched_at"] = now
            # 注意：不清除 updated_at 缓存

    updatable = latest is not None and latest != "unknown" and latest != current
    return {
        "current": current,
        "latest": latest,
        "updatable": updatable,
        "updated_at": ""  # 明确不返回
    }

# ===== 接口2：/version/lastVersion （按需获取时间）=====
@router.get("/lastVersion")
async def get_version_with_time():
    now = datetime.now()
    current = get_current_version()

    async with _cache_lock:
        # 1. 确保版本是最新的
        if (
                _cache["latest_version"] is None or
                _cache["fetched_at"] is None or
                (now - _cache["fetched_at"]) >= timedelta(seconds=CACHE_TTL)
        ):
            latest = await _fetch_latest_version()
            _cache["latest_version"] = latest
            _cache["fetched_at"] = now
        else:
            latest = _cache["latest_version"]

        # 2. 检查时间缓存是否有效
        need_fetch_time = (
                _cache["updated_at"] is None or
                _cache["time_fetched_at"] is None or
                (now - _cache["time_fetched_at"]) >= timedelta(seconds=CACHE_TTL)
        )

        if need_fetch_time:
            updated_at = await _fetch_updated_at()
            _cache["updated_at"] = updated_at
            _cache["time_fetched_at"] = now
        else:
            updated_at = _cache["updated_at"]

    updatable = latest is not None and latest != "unknown" and latest != current
    return {
        "current": current,
        "latest": latest,
        "updatable": updatable,
        "updated_at": updated_at or ""
    }
