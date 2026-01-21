import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-123")

def get_db_connection():
    db_url = os.environ.get("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")

    if not db_url:
        print("❌ DATABASE_URL is None at runtime")
        return None

    return psycopg2.connect(
        db_url,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
