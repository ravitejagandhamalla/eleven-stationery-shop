import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    database_url = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")

    if not database_url:
        # Do NOT crash the app on import
        raise RuntimeError("DATABASE_URL environment variable is missing")

    return psycopg2.connect(
        database_url,
        sslmode="require",
        cursor_factory=RealDictCursor
    )

