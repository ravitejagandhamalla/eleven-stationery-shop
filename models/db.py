import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-123")

DATABASE_URL = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:Rohiit141645@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")

def get_db_connection():
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL not found in environment variables")
        return None

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require"
    )
