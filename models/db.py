import os
import psycopg2
import psycopg2.extras

def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require"
    )
    return conn
