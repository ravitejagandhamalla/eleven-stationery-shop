import os
from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():
    database_url = os.environ.get("postgresql://ravi_teja_user:8OVmBnpToXXuq3qAiL9SmMof3AYD8NvO@dpg-d69va7vpm1nc739obqa0-a.virginia-postgres.render.com/ravi_teja")

    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return None

    return psycopg2.connect(
        database_url,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )


# ==============================
# HOME
# ==============================

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        if not conn:
            return "Database connection error"

        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, password)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        if not conn:
            return "Database connection error"

        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password"

    return render_template("login.html")


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==============================
# REMOVE THIS FOR RENDER
# ==============================

# DO NOT run app.run() on Render
# Gunicorn will handle it
