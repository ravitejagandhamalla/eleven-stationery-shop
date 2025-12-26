from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"

# ---------------- LOGIN REQUIRED DECORATOR ----------------

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first!", "error")
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
@login_required
def change_password():
    if request.method == "POST":
        old_pass = request.form["old_password"].strip()
        new_pass = request.form["new_password"].strip()
        confirm_pass = request.form["confirm_password"].strip()

        if new_pass != confirm_pass:
            flash("New passwords do not match!", "error")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (session["user"], old_pass)
        ).fetchone()

        if not user:
            flash("Old password incorrect!", "error")
            conn.close()
            return redirect(url_for("change_password"))

        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_pass, session["user"])
        )
        conn.commit()
        conn.close()

        flash("Password changed successfully!", "success")
        return redirect(url_for("index"))

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


# ---------------- INCOME ----------------

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

        flash("Income added!", "success")
        return redirect(url_for("view_records", t="income"))

    return render_template("income.html", edit=False)


# ---------------- EXPENSE ----------------

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

        flash("Expense added!", "success")
        return redirect(url_for("view_records", t="expenses"))

    return render_template("expense.html", edit=False)


# ---------------- VIEW RECORDS ----------------

@app.route("/records")
@login_required
def view_records():
    t = request.args.get("t", "both")

    conn = get_db_connection()
    incomes = conn.execute("SELECT * FROM income ORDER BY date DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()

    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses,
        t=t
    )


# ---------------- SUMMARY ----------------

@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()

    total_income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM income"
    ).fetchone()[0]

    total_expense = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        profit=total_income - total_expense
    )


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
