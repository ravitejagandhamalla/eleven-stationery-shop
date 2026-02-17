import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from urllib.parse import urlparse

# -------------------------------------------------
# Load Environment Variables
# -------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

DATABASE_URL = os.getenv("postgresql://ravi_teja_user:8OVmBnpToXXuq3qAiL9SmMof3AYD8NvO@dpg-d69va7vpm1nc739obqa0-a.virginia-postgres.render.com/ravi_teja")


# -------------------------------------------------
# Database Connection Function
# -------------------------------------------------
def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    # Fix for Render (ensures sslmode=require)
    if DATABASE_URL.startswith("postgres://"):
        db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        db_url = DATABASE_URL

    return psycopg2.connect(db_url, sslmode="require")


# -------------------------------------------------
# Routes
# -------------------------------------------------

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user"] = user["email"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password")
            return redirect(url_for("login"))

    return render_template("login.html")


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=session["user"])


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------
# Forgot Password (Optional)
# -------------------------------------------------
@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


# -------------------------------------------------
# Change Password (Optional)
# -------------------------------------------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        email = request.form.get("email")
        new_password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (new_password, email)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Password updated successfully")
        return redirect(url_for("login"))

    return render_template("change_password.html")


# -------------------------------------------------
# Run Locally
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
