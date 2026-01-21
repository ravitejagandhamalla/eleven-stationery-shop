import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, session

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-123")

DATABASE_URL = os.environ.get("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")


# -------------------------------------------------
# DB CONNECTION
# -------------------------------------------------
def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    return psycopg2.connect(
        dsn=DATABASE_URL,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )


# -------------------------------------------------
# LOGIN REQUIRED DECORATOR
# -------------------------------------------------
def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
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
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

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
        email = request.form.get("email")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
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
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if new_password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("reset_password"))

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (new_password, session["reset_email"])
        )

        conn.commit()
        cur.close()
        conn.close()

        session.pop("reset_email")
        flash("Password reset successful")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


# -------------------------------------------------
# CHANGE PASSWORD (LOGGED IN)
# -------------------------------------------------
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form.get("old_password")
        new = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        if new != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (session["user_email"], old)
        )
        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            flash("Old password incorrect", "error")
            return redirect(url_for("change_password"))

        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (new, session["user_email"])
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
# RUN LOCAL ONLY
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
