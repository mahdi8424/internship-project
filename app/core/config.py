import os

from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db",
)

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-development-secret",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "15",
    )
)

REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv(
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "7",
    )
)