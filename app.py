import os
import psycopg2
import psycopg2.extras
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-123")

app = Flask(__name__)
app.secret_key = SECRET_KEY


# -------------------------------------------------
# DB CONNECTION
# -------------------------------------------------
def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require"
    )


# -------------------------------------------------
# LOGIN REQUIRED
# -------------------------------------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
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
            session["user_email"] = email
            return redirect(url_for("index"))

        flash("Invalid email or password", "error")

    return render_template("login.html")


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------
# FORGOT PASSWORD
# -------------------------------------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            flash("Email not found", "error")
            return redirect(url_for("forgot_password"))

        session["reset_email"] = email
        return redirect(url_for("reset_password"))

    return render_template("forgot_password.html")


# -------------------------------------------------
# RESET PASSWORD
# -------------------------------------------------
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if new != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("reset_password"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new, session["reset_email"])
        )
        conn.commit()
        cur.close()
        conn.close()

        session.pop("reset_email")
        flash("Password reset successful")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


# -------------------------------------------------
# CHANGE PASSWORD
# -------------------------------------------------
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]
        email = session["user_email"]

        if new != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email=%s AND password=%s",
            (email, old)
        )
        user = cur.fetchone()

        if not user:
            flash("Old password incorrect", "error")
            cur.close()
            conn.close()
            return redirect(url_for("change_password"))

        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new, email)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Password changed successfully")
        return redirect(url_for("index"))

    return render_template("change_password.html")


# -------------------------------------------------
# HOME
# -------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
