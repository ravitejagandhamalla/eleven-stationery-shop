import os
import psycopg2
import psycopg2.extras
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

# -------------------------------------------------
# ENV SETUP
# -------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("postgresql://postgres.vjmksejmnxgowpnwgaxv:dlmHeBHcR0IWx8Jm@aws-1-ap-south-1.pooler.supabase.com:5432/postgres")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-123")

# -------------------------------------------------
# APP INIT
# -------------------------------------------------
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
# LOGIN REQUIRED DECORATOR
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
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["user_email"] = user["email"]
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
# CHANGE PASSWORD
# -------------------------------------------------
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        email = session["user_email"]
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

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
            cur.close()
            conn.close()
            flash("Old password incorrect", "error")
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
# ADD INCOME
# -------------------------------------------------
@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO income (date, amount, description) VALUES (%s, %s, %s)",
            (
                request.form["date"],
                request.form["amount"],
                request.form["description"]
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("view_records", t="income"))

    return render_template("income.html", edit=False)


# -------------------------------------------------
# ADD EXPENSE
# -------------------------------------------------
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (%s, %s, %s)",
            (
                request.form["date"],
                request.form["amount"],
                request.form["purpose"]
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("view_records", t="expenses"))

    return render_template("expense.html", edit=False)


# -------------------------------------------------
# VIEW RECORDS
# -------------------------------------------------
@app.route("/records")
@login_required
def view_records():
    t = request.args.get("t", "both")
    conn = get_db_connection()
    cur = conn.cursor()

    incomes = []
    expenses = []

    if t in ("income", "both"):
        cur.execute("SELECT * FROM income ORDER BY date DESC")
        incomes = cur.fetchall()

    if t in ("expenses", "both"):
        cur.execute("SELECT * FROM expenses ORDER BY date DESC")
        expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses,
        t=t
    )


# -------------------------------------------------
# DELETE RECORD
# -------------------------------------------------
@app.route("/delete/<string:typ>/<int:id>", methods=["POST"])
@login_required
def delete_record(typ, id):
    conn = get_db_connection()
    cur = conn.cursor()

    if typ == "income":
        cur.execute("DELETE FROM income WHERE id=%s", (id,))
    else:
        cur.execute("DELETE FROM expenses WHERE id=%s", (id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("view_records", t=typ))


# -------------------------------------------------
# SUMMARY
# -------------------------------------------------
@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM income")
    total_income = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses")
    total_expense = cur.fetchone()["coalesce"]

    cur.close()
    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense
    )


# -------------------------------------------------
# RUN LOCAL
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
