from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.db import get_db_connection

app = Flask(__name__)
app.secret_key = "eleven_stationery_secret"


# ================= LOGIN REQUIRED =================

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            session.clear()
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

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
        conn.close()

        if user:
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))


# ================= CHANGE PASSWORD =================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        username = request.form["username"]
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if new != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, old)
        )
        if not cur.fetchone():
            conn.close()
            flash("Invalid credentials", "error")
            return redirect(url_for("change_password"))

        cur.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new, username)
        )
        conn.commit()
        conn.close()

        flash("Password updated", "success")
        return redirect(url_for("login"))

    return render_template("change_password.html")


# ================= HOME =================

@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ================= ADD INCOME =================

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
        flash("Income added", "success")
        return redirect(url_for("records", t="income"))

    return render_template("income.html", edit=False)


# ================= ADD EXPENSE =================

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
        flash("Expense added", "success")
        return redirect(url_for("records", t="expenses"))

    return render_template("expense.html", edit=False)


# ================= EDIT INCOME =================

@app.route("/edit/income/<int:id>", methods=["GET", "POST"])
@login_required
def edit_income(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM income WHERE id=%s", (id,))
    record = cur.fetchone()

    if request.method == "POST":
        cur.execute(
            "UPDATE income SET date=%s, amount=%s, description=%s WHERE id=%s",
            (request.form["date"], request.form["amount"], request.form["description"], id)
        )
        conn.commit()
        conn.close()
        flash("Income updated", "success")
        return redirect(url_for("records", t="income"))

    conn.close()
    return render_template("income.html", record=record, edit=True)


# ================= EDIT EXPENSE =================

@app.route("/edit/expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id=%s", (id,))
    record = cur.fetchone()

    if request.method == "POST":
        cur.execute(
            "UPDATE expenses SET date=%s, amount=%s, purpose=%s WHERE id=%s",
            (request.form["date"], request.form["amount"], request.form["purpose"], id)
        )
        conn.commit()
        conn.close()
        flash("Expense updated", "success")
        return redirect(url_for("records", t="expenses"))

    conn.close()
    return render_template("expense.html", record=record, edit=True)


# ================= DELETE =================

@app.route("/delete/<string:typ>/<int:id>", methods=["POST"])
@login_required
def delete_record(typ, id):
    conn = get_db_connection()
    cur = conn.cursor()

    if typ == "income":
        cur.execute("DELETE FROM income WHERE id=%s", (id,))
    elif typ == "expenses":
        cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
    else:
        conn.close()
        flash("Invalid delete", "error")
        return redirect(url_for("records"))

    conn.commit()
    conn.close()
    flash("Deleted successfully", "success")
    return redirect(url_for("records", t=typ))


# ================= VIEW RECORDS + FILTER =================

@app.route("/records")
@login_required
def records():
    t = request.args.get("t", "both")
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db_connection()
    cur = conn.cursor()

    def fetch(table):
        sql = f"SELECT * FROM {table}"
        params = []
        if start and end:
            sql += " WHERE date BETWEEN %s AND %s"
            params = [start, end]
        sql += " ORDER BY date DESC"
        cur.execute(sql, params)
        return cur.fetchall()

    incomes = fetch("income") if t in ("income", "both") else []
    expenses = fetch("expenses") if t in ("expenses", "both") else []

    conn.close()
    return render_template("view_records.html", incomes=incomes, expenses=expenses, t=t)


# ================= SUMMARY =================

@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) total FROM income")
    total_income = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses")
    total_expense = cur.fetchone()["total"]

    cur.execute("""
        SELECT
            d.date,
            COALESCE(i.total,0) inc,
            COALESCE(e.total,0) exp
        FROM (
            SELECT date FROM income
            UNION
            SELECT date FROM expenses
        ) d
        LEFT JOIN (SELECT date, SUM(amount) total FROM income GROUP BY date) i ON d.date=i.date
        LEFT JOIN (SELECT date, SUM(amount) total FROM expenses GROUP BY date) e ON d.date=e.date
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


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)


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
