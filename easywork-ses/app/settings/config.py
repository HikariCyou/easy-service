import os
import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "SESシステム"
    PROJECT_NAME: str = "Tob-HR"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    UPLOAD_DIR: str = "uploaded_files"

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32

    SERVER_HOST: str = "54.248.142.194"
    DOMAIN_HOST: str = "etalk.tob.co.jp"

    # External Service URLs
    # SSO_BASE_URL: str = "http://13.158.219.191:8081/admin-api/system"
    # PROCESS_BASE_URL: str = "http://13.158.219.191:8081/admin-api/bpm/starter"

    SSO_BASE_URL: str = "http://localhost:48080/admin-api/system"
    PROCESS_BASE_URL: str = "http://localhost:48080/admin-api/bpm/starter"

    TORTOISE_ORM: dict = {
        "connections": {
            # SQLite configuration
            # "sqlite": {
            #     "engine": "tortoise.backends.sqlite",
            #     "credentials": {"file_path": f"{BASE_DIR}/db.sqlite3"},  # Path to SQLite database file
            # },
            # MySQL/MariaDB configuration
            # Install with: tortoise-orm[asyncmy]
            "mysql": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": SERVER_HOST,  # Database host address
                    "port": 42106,  # Database port
                    "user": "root",  # Database username
                    "password": "JaTobpanese001.,.",  # Database password
                    "database": "easywork-main",  # Database name
                },
            },
            # PostgreSQL configuration
            # Install with: tortoise-orm[asyncpg]
            # "postgres": {
            #     "engine": "tortoise.backends.asyncpg",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 5432,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
            # MSSQL/Oracle configuration
            # Install with: tortoise-orm[asyncodbc]
            # "oracle": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
            # SQLServer configuration
            # Install with: tortoise-orm[asyncodbc]
            # "sqlserver": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
        },
        "apps": {
            "models": {
                "models": ["app.models", "aerich.models"],
                "default_connection": "mysql",
            },
        },
        "use_tz": True,  # Whether to use timezone-aware datetimes
        "timezone": "Asia/Tokyo",  # Timezone setting
    }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


settings = Settings()
