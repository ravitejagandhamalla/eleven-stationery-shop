from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.db import get_db_connection

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"


# ================= LOGIN REQUIRED =================
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            session.clear()
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ================= LOGIN (ONLY ONE) =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = username
            flash("Login successful", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))


# ================= HOME =================
@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ================= INCOME =================
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

    return render_template("income.html", edit=False)


# ================= EXPENSE =================
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

    return render_template("expense.html", edit=False)


# ================= RECORDS =================
@app.route("/records")
@login_required
def records():
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

    conn.close()
    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses,
        t=t
    )


# ================= SUMMARY =================
@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM income")
    total_income = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses")
    total_expense = cur.fetchone()[0]

    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense
    )


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
