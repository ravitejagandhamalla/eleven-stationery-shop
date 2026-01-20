from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "eleven_stationery_secret"


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
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form["username"], request.form["password"])
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            return redirect(url_for("index"))

        flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- HOME ----------------
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
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO income (date, amount, description) VALUES (%s,%s,%s)",
            (request.form["date"], request.form["amount"], request.form["description"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records", t="income"))

    return render_template("income.html")


# ---------------- ADD EXPENSE ----------------
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (%s,%s,%s)",
            (request.form["date"], request.form["amount"], request.form["purpose"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records", t="expenses"))

    return render_template("expense.html")


# ---------------- RECORDS ----------------
@app.route("/records")
@login_required
def records():
    t = request.args.get("t", "both")
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db_connection()
    cur = conn.cursor()

    where = []
    params = []

    if start:
        where.append("date >= %s")
        params.append(start)
    if end:
        where.append("date <= %s")
        params.append(end)

    clause = " WHERE " + " AND ".join(where) if where else ""

    incomes = []
    expenses = []

    if t in ("income", "both"):
        cur.execute("SELECT * FROM income" + clause + " ORDER BY date DESC", params)
        incomes = cur.fetchall()

    if t in ("expenses", "both"):
        cur.execute("SELECT * FROM expenses" + clause + " ORDER BY date DESC", params)
        expenses = cur.fetchall()

    conn.close()
    return render_template("view_records.html", incomes=incomes, expenses=expenses, t=t)


# ---------------- SUMMARY ----------------
@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM income")
    total_income = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM expenses")
    total_expense = cur.fetchone()["total"]

    cur.execute("""
        SELECT d.date,
        COALESCE(SUM(i.amount),0) AS inc,
        COALESCE(SUM(e.amount),0) AS exp
        FROM (
            SELECT date FROM income
            UNION
            SELECT date FROM expenses
        ) d
        LEFT JOIN income i ON i.date=d.date
        LEFT JOIN expenses e ON e.date=d.date
        GROUP BY d.date
        ORDER BY d.date DESC
    """)
    daily = cur.fetchall()

    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense,
        daily=daily
    )


if __name__ == "__main__":
    app.run()
