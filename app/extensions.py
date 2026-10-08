import os

import psycopg
from psycopg.rows import dict_row


def get_database_url():
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/ricoz_store",
    )


def get_db_connection():
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )