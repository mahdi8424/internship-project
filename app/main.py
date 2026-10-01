from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.users import router as users_router


app = FastAPI(
    title="Project Management API",
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(users_router)