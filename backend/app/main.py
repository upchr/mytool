# backend/app/main.py
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.core.exception.exception_handler import setup_exception_handlers
from app.modules.note.api import router as note_router
from app.modules.cron.api import router as cron_router
from app.modules.database.api import router as database_router
from app.modules.version.api import router as version_router
from app.modules.notify.api import router as notify_router
from app.modules.node.api import router as node_router


"""日志调用"""
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """日志配置"""
    from app.core.log.log import setup_logging
    from app.core.config import get_config

    config_obj = get_config()
    setup_logging(config_obj)

    logger.info("应用启动中...")
    import os
    logger.info(f"启动成功进程id: {os.getpid()}")

    # 数据库初始
    from app.core.db.init_db import init_database
    init_database()

    # ws配置
    from app.core.ws.ws_manager import ws_manager
    ws_manager.set_event_loop(asyncio.get_running_loop())

    # 定时任务配置
    from app.modules.cron.scheduler import scheduler
    scheduler.start()

    # fastapi
    yield

    logger.info("应用正在关闭...")
    scheduler.shutdown()

app = FastAPI(title="Note App", lifespan=lifespan)

"""跨域"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

"""全局异常处理"""
setup_exception_handlers(app)

"""路由配置"""
app.include_router(note_router)
app.include_router(cron_router)
app.include_router(node_router)
app.include_router(database_router)
app.include_router(version_router)
app.include_router(notify_router)


"""启动main，项目目录为app上级"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
