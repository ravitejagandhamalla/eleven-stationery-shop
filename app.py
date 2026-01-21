import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

# -------------------------------------------------
# ENV SETUP
# -------------------------------------------------
load_dotenv()

DATABASE_URL = os.environ.get("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-123")

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY


# -------------------------------------------------
# DATABASE CONNECTION (SAFE – NO CRASH)
# -------------------------------------------------
def get_db_connection():
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL not set")
        return None

    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )


# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error", "danger")
            return redirect(url_for("login"))

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", email=session.get("email"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
