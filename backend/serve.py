from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.core.exception.exception_handler import setup_exception_handlers
from app.core.middleware.auth import jwt_auth_middleware, check_initialization_middleware

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.log.log import setup_logging
    from app.core.config import get_config
    config_obj = get_config()
    setup_logging(config_obj)
    logger.info("应用启动中...")
    
    from app.core.db.init_db import init_database
    init_database()
    
    from app.core.ws.ws_manager import ws_manager
    ws_manager.set_event_loop(asyncio.get_running_loop())
    
    from app.core.scheduler.config import init_schedule, destroy_schedule
    init_schedule()
    
    try:
        from app.core.db.database import get_engine
        from app.modules.cpe.services import CPEMonitorService
        CPEMonitorService.auto_start_monitor(get_engine())
    except Exception as e:
        logger.warning(f"CPE 自动监控启动失败: {e}")
    
    from app.core.routers import router_manager
    router_manager.register_routers(app)
    
    from datetime import datetime
    from app.core.db.database import get_engine
    from app.modules.sys.models import system_config_table
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                system_config_table.update()
                .where(system_config_table.c.id == 1)
                .values(app_start_time=datetime.now())
            )
        logger.info("应用启动时间已记录")
    except Exception as e:
        logger.warning(f"记录应用启动时间失败: {e}")
    
    yield
    
    logger.info("应用正在关闭...")
    destroy_schedule()

app = FastAPI(title="ToolsPlus", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)
app.middleware("http")(jwt_auth_middleware)
app.middleware("http")(check_initialization_middleware)

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets"), html=False), name="assets")
    app.mount("/favicon.ico", StaticFiles(directory=str(FRONTEND_DIST), html=False, follow_symlink=True), name="favicon")

@app.get("/")
async def serve_index():
    if FRONTEND_DIST.exists():
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    return {"message": "ToolsPlus API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serve:app", host="0.0.0.0", port=8000, reload=False)
