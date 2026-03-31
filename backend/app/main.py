# backend/app/main.py
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.core.exception.exception_handler import setup_exception_handlers
from app.core.middleware.auth import jwt_auth_middleware, check_initialization_middleware
# from app.modules.note.api import router as note_router
# from app.modules.cron.api import router as cron_router
# from app.modules.database.api import router as database_router
# from app.modules.version.api import router as version_router
# from app.modules.notify.api import router as notify_router
# from app.modules.node.api import router as node_router
# from app.modules.example import router as example_router
# from app.modules.sys import router as sys_router
# from app.modules.acme.api import router as ssl_router

"""日志调用"""
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 启动阶段 ---
    # 1. 日志配置
    from app.core.log.log import setup_logging
    from app.core.config import get_config
    import os
    config_obj = get_config()
    setup_logging(config_obj)

    logger.info("应用启动中...")
    logger.info(f"启动成功进程id: {os.getpid()}")

    from app.core.utils.path_utils import path_utils
    path_utils.print_paths()

    # 2. 数据库初始化
    from app.core.db.init_db import init_database
    init_database()

    # 3. WebSocket 配置
    from app.core.ws.ws_manager import ws_manager
    ws_manager.set_event_loop(asyncio.get_running_loop())

    # 4. 定时任务配置
    from app.core.scheduler.config import init_schedule,destroy_schedule
    init_schedule()

    # 5. CPE 自动监控启动
    try:
        from app.core.db.database import get_engine
        from app.modules.cpe.services import CPEMonitorService
        CPEMonitorService.auto_start_monitor(get_engine())
    except Exception as e:
        logger.warning(f"CPE 自动监控启动失败: {e}")

    # 6. 路由配置
    from app.core.routers import router_manager
    router_manager.register_routers(app)

    # 7. 记录应用启动时间
    from datetime import datetime
    from app.core.db.database import get_engine
    from app.modules.sys.models import system_config_table
    try:
        engine = get_engine()
        with engine.begin() as conn:
            # 更新应用启动时间
            conn.execute(
                system_config_table.update()
                .where(system_config_table.c.id == 1)
                .values(app_start_time=datetime.now())
            )
        logger.info("应用启动时间已记录")
    except Exception as e:
        logger.warning(f"记录应用启动时间失败: {e}")

    # 运行应用
    yield

    # --- 关闭阶段 ---
    logger.info("应用正在关闭...")
    # 关闭调度器
    destroy_schedule()


app = FastAPI(title="Note App", lifespan=lifespan)

"""跨域"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://upchr.github.io",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""全局异常处理"""
setup_exception_handlers(app)

app.middleware("http")(jwt_auth_middleware)
app.middleware("http")(check_initialization_middleware)

# """路由配置"""
# app.include_router(note_router)
# app.include_router(cron_router)
# app.include_router(node_router)
# app.include_router(database_router)
# app.include_router(version_router)
# app.include_router(notify_router)
# app.include_router(example_router)
# app.include_router(sys_router)
# app.include_router(ssl_router)


"""启动main，项目目录为app上级"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
