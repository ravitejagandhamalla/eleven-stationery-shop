import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ========================
# CONFIG
# ========================
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-123")

DATABASE_URL = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# ========================
# DATABASE CONNECTION
# ========================
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ========================
# ROUTES
# ========================

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

# ------------------------
# LOGIN
# ------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# ------------------------
# LOGOUT
# ------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------------
# CHANGE PASSWORD (FIXED)
# ------------------------
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password=%s WHERE id=%s",
            (new_password, session["user_id"])
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Password updated successfully", "success")
        return redirect(url_for("index"))

    return render_template("change_password.html")

# ========================
# RUN
# ========================
if __name__ == "__main__":
    app.run(debug=True)
