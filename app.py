from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"


# ---------------- LOGIN REQUIRED ----------------

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- CHANGE PASSWORD ----------------
# 🔴 THIS ROUTE WAS MISSING – NOW FIXED

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        username = request.form["username"]
        old = request.form["old_password"]
        new = request.form["new_password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, old)
        ).fetchone()

        if not user:
            conn.close()
            flash("Wrong credentials", "error")
            return redirect(url_for("change_password"))

        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new, username)
        )
        conn.commit()
        conn.close()

        flash("Password updated", "success")
        return redirect(url_for("login"))

    return render_template("change_password.html")


# ---------------- HOME / DASHBOARD ----------------

@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ---------------- ADD INCOME ----------------

@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO income (date, amount, description) VALUES (?, ?, ?)",
            (request.form["date"], request.form["amount"], request.form["description"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    return render_template("income.html")


# ---------------- ADD EXPENSE ----------------

@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (?, ?, ?)",
            (request.form["date"], request.form["amount"], request.form["purpose"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    return render_template("expense.html")


# ---------------- VIEW RECORDS ----------------
# 🔴 FUNCTION NAME IS `records` (NOT view_records)

@app.route("/records")
@login_required
def records():
    conn = get_db_connection()
    incomes = conn.execute("SELECT * FROM income ORDER BY date DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()

    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses
    )


# ---------------- SUMMARY ----------------

@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()

    total_income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
    total_expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]

    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense
    )
