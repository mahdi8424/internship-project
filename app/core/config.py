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

LOGIN_RATE_LIMIT = int(
    os.getenv(
        "LOGIN_RATE_LIMIT",
        "5",
    )
)
LOGIN_RATE_WINDOW_SECONDS = int(
    os.getenv(
        "LOGIN_RATE_WINDOW_SECONDS",
        "60",
    )
)

ADMIN_EMAIL = os.getenv(
        "ADMIN_EMAIL",
        "admin@example.com",
    )

ADMIN_PASSWORD = os.getenv(
        "ADMIN_PASSWORD",
    )

ADMIN_FULL_NAME = os.getenv(
        "ADMIN_FULL_NAME",
        "System Admin",
    )
