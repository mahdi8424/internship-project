import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.tasks import (
    project_tasks_router,
    tasks_router,
)
from app.api.routes.users import router as users_router
from app.core.config import (
    ADMIN_EMAIL,
    ADMIN_FULL_NAME,
    ADMIN_PASSWORD,
)
from app.core.logging import setup_logging
from app.db.bootstrap import create_initial_admin
from app.db.session import SessionLocal


setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is not configured"
        )

    db = SessionLocal()

    try:
        create_initial_admin(
            db=db,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            full_name=ADMIN_FULL_NAME,
        )

        logger.info(
            "Initial admin verified: %s",
            ADMIN_EMAIL,
        )
    finally:
        db.close()

    yield


app = FastAPI(
    title="Project Management API",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        },
    )


app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(project_tasks_router)
app.include_router(tasks_router)
app.include_router(users_router)