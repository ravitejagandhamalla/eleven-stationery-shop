from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"


# ---------------- LOGIN REQUIRED DECORATOR ----------------
@app.before_request
def require_login():
    allowed = {"login", "forgot_password", "reset_password", "static"}
    if request.endpoint not in allowed and "user" not in session:
        return redirect(url_for("login"))

def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first!", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper



# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()  # 🔐 clears old cookies / sessions

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
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------------- CHANGE PASSWORD ----------------

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        username = request.form["username"].strip()
        old_pass = request.form["old_password"].strip()
        new_pass = request.form["new_password"].strip()
        confirm_pass = request.form["confirm_password"].strip()

        if new_pass != confirm_pass:
            flash("Passwords do not match!", "error")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, old_pass)
        ).fetchone()

        if not user:
            flash("Invalid username or old password!", "error")
            conn.close()
            return redirect(url_for("change_password"))

        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_pass, username)
        )
        conn.commit()
        conn.close()

        flash("Password changed successfully!", "success")
        return redirect(url_for("login"))

    return render_template("change_password.html")


# ---------------- FORGOT PASSWORD ----------------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"].strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if not user:
            flash("Username not found!", "error")
            return redirect(url_for("forgot_password"))

        session["reset_user"] = username
        return redirect(url_for("reset_password"))

    return render_template("forgot_password.html")


# ---------------- RESET PASSWORD ----------------

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_user" not in session:
        flash("Unauthorized access!", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_pass = request.form["new_password"].strip()
        confirm_pass = request.form["confirm_password"].strip()

        if new_pass != confirm_pass:
            flash("Passwords do not match!", "error")
            return redirect(url_for("reset_password"))

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_pass, session["reset_user"])
        )
        conn.commit()
        conn.close()

        session.pop("reset_user", None)
        flash("Password reset successfully!", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


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
        conn.execute(
            "INSERT INTO income (date, amount, description) VALUES (?, ?, ?)",
            (
                request.form["date"],
                request.form["amount"],
                request.form["description"]
            )
        )
        conn.commit()
        conn.close()

        flash("Income added!", "success")
        return redirect(url_for("view_records", t="income"))

    return render_template("income.html", edit=False)


# ---------------- ADD EXPENSE ----------------

@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (?, ?, ?)",
            (
                request.form["date"],
                request.form["amount"],
                request.form["purpose"]
            )
        )
        conn.commit()
        conn.close()

        flash("Expense added!", "success")
        return redirect(url_for("view_records", t="expenses"))

    return render_template("expense.html", edit=False)


# ---------------- EDIT INCOME ----------------

@app.route("/edit/income/<int:id>", methods=["GET", "POST"])
@login_required
def edit_income(id):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM income WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE income SET date=?, amount=?, description=? WHERE id=?",
            (
                request.form["date"],
                request.form["amount"],
                request.form["description"],
                id
            )
        )
        conn.commit()
        conn.close()

        flash("Income updated!", "success")
        return redirect(url_for("view_records", t="income"))

    conn.close()
    return render_template("income.html", record=record, edit=True)


# ---------------- EDIT EXPENSE ----------------

@app.route("/edit/expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM expenses WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE expenses SET date=?, amount=?, purpose=? WHERE id=?",
            (
                request.form["date"],
                request.form["amount"],
                request.form["purpose"],
                id
            )
        )
        conn.commit()
        conn.close()

        flash("Expense updated!", "success")
        return redirect(url_for("view_records", t="expenses"))

    conn.close()
    return render_template("expense.html", record=record, edit=True)


# ---------------- DELETE RECORD ----------------

@app.route("/delete/<string:typ>/<int:id>", methods=["POST"])
@login_required
def delete_record(typ, id):
    conn = get_db_connection()

    if typ == "income":
        conn.execute("DELETE FROM income WHERE id=?", (id,))
    elif typ == "expenses":
        conn.execute("DELETE FROM expenses WHERE id=?", (id,))
    else:
        conn.close()
        flash("Invalid delete request!", "error")
        return redirect(url_for("view_records"))

    conn.commit()
    conn.close()
    flash("Record deleted!", "success")
    return redirect(url_for("view_records", t=typ))


# ---------------- VIEW RECORDS ----------------

@app.route("/records")
@login_required
def view_records():
    t = request.args.get("t", "both")
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db_connection()

    filter_sql = ""
    params = []

    if start and end:
        filter_sql = " WHERE date BETWEEN ? AND ? "
        params = [start, end]
    elif start:
        filter_sql = " WHERE date >= ? "
        params = [start]
    elif end:
        filter_sql = " WHERE date <= ? "
        params = [end]

    incomes = []
    expenses = []

    if t in ("income", "both"):
        incomes = conn.execute(
            "SELECT * FROM income" + filter_sql + " ORDER BY date DESC",
            params
        ).fetchall()

    if t in ("expenses", "both"):
        expenses = conn.execute(
            "SELECT * FROM expenses" + filter_sql + " ORDER BY date DESC",
            params
        ).fetchall()

    conn.close()

    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses,
        t=t,
        start=start,
        end=end
    )


# ---------------- SUMMARY ----------------

@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()

    total_income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM income"
    ).fetchone()[0]

    total_expense = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses"
    ).fetchone()[0]

    profit = total_income - total_expense

    daily = conn.execute("""
        SELECT 
            d.date,
            COALESCE(i.total_income, 0) AS income,
            COALESCE(e.total_expense, 0) AS expense
        FROM (
            SELECT date FROM income
            UNION
            SELECT date FROM expenses
        ) d
        LEFT JOIN (
            SELECT date, SUM(amount) AS total_income
            FROM income
            GROUP BY date
        ) i ON d.date = i.date
        LEFT JOIN (
            SELECT date, SUM(amount) AS total_expense
            FROM expenses
            GROUP BY date
        ) e ON d.date = e.date
        ORDER BY d.date DESC
    """).fetchall()

    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=profit,
        daily=daily
    )



# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)
