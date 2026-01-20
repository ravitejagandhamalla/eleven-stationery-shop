import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:Ravi141645DB@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require"
    )
