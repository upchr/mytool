# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.note.api import router as note_router
from app.modules.cron.api import router as cron_router
from contextlib import asynccontextmanager
from app.modules.cron.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    scheduler.start()
    yield
    # 关闭时
    scheduler.shutdown()

app = FastAPI(title="Note App", lifespan=lifespan)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(note_router)
app.include_router(cron_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
