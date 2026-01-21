import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.db import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-123")


# ---------------- LOGIN REQUIRED ----------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first", "error")
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
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
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
            "INSERT INTO income (date, amount, description) VALUES (%s, %s, %s)",
            (request.form["date"], request.form["amount"], request.form["description"])
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("view_records", t="income"))

    return render_template("income.html", edit=False)


# ---------------- ADD EXPENSE ----------------
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (%s, %s, %s)",
            (request.form["date"], request.form["amount"], request.form["purpose"])
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("view_records", t="expenses"))

    return render_template("expense.html", edit=False)


# ---------------- VIEW RECORDS ----------------
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


# ---------------- EDIT INCOME ----------------
@app.route("/edit/income/<int:id>", methods=["GET", "POST"])
@login_required
def edit_income(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "UPDATE income SET date=%s, amount=%s, description=%s WHERE id=%s",
            (request.form["date"], request.form["amount"], request.form["description"], id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("view_records", t="income"))

    cur.execute("SELECT * FROM income WHERE id=%s", (id,))
    record = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("income.html", record=record, edit=True)


# ---------------- EDIT EXPENSE ----------------
@app.route("/edit/expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            "UPDATE expenses SET date=%s, amount=%s, purpose=%s WHERE id=%s",
            (request.form["date"], request.form["amount"], request.form["purpose"], id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("view_records", t="expenses"))

    cur.execute("SELECT * FROM expenses WHERE id=%s", (id,))
    record = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("expense.html", record=record, edit=True)


# ---------------- DELETE ----------------
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


# ---------------- SUMMARY ----------------
@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM income")
    total_income = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
    total_expense = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense
    )


if __name__ == "__main__":
    app.run(debug=True)
