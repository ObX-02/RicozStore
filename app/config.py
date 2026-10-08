import os


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "ricoz-store-development-secret",
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/ricoz_store",
    )

    RICOZ_STORE_NAME = "RicozStore"