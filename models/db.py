import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("postgresql://postgres.vjmksejmnxgowpnwgaxv:Ravi141645%24@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")

def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require"
    )
