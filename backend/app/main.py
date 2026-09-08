import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.database import init_db
from backend.app.core.config import settings
from backend.app.services.telegram_service import TelegramBotService
from backend.app.services.tracker_worker import TrackerWorker
from backend.app.api import routes_config, routes_bot, routes_tokens

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

telegram_service = TelegramBotService()
tracker_worker = TrackerWorker(telegram_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Memecoin Tracker Backend...")
    await init_db()

    # Initialize Telegram Bot
    await telegram_service.init_application()

    # Store references in app state
    app.state.telegram_service = telegram_service
    app.state.tracker_worker = tracker_worker

    # Start background polling worker
    worker_task = asyncio.create_task(tracker_worker.start())

    yield

    # Shutdown
    logger.info("Shutting down Memecoin Tracker Backend...")
    tracker_worker.is_running = False
    worker_task.cancel()
    if telegram_service.app:
        try:
            await telegram_service.app.stop()
            await telegram_service.app.shutdown()
        except Exception:
            pass

app = FastAPI(
    title="Solana Memecoin Tracker API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(routes_config.router)
app.include_router(routes_bot.router)
app.include_router(routes_tokens.router)

@app.get("/")
async def root():
    return {"message": "Solana Memecoin Tracker API is running 🚀", "docs": "/docs"}
