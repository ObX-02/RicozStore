
import os

import psycopg
from psycopg.rows import dict_row


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not configured."
        )

    return database_url


def get_db_connection():
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )