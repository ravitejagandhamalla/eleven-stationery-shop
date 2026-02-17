import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "super-secret-key-123"


# ==============================
# DATABASE CONNECTION
# ==============================
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )
    return conn



# ==============================
# HOME
# ==============================
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM users WHERE username=%s AND password=%s",
                (username, password),
            )
            user = cur.fetchone()

            cur.close()
            conn.close()

            if user:
                session["user_id"] = user[0]
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password")

        except Exception as e:
            return "Database connection error"

    return render_template("login.html")


# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==============================
# DASHBOARD
# ==============================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=%s",
        (session["user_id"],)
    )
    total_income = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s",
        (session["user_id"],)
    )
    total_expense = cur.fetchone()[0]

    balance = total_income - total_expense

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )



# ==============================
# ADD INCOME
# ==============================
@app.route("/income", methods=["GET", "POST"])
def income():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form["amount"]
        description = request.form["description"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO income (user_id, amount, description) VALUES (%s, %s, %s)",
            (session["user_id"], amount, description),
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Income added successfully")
        return redirect(url_for("dashboard"))

    return render_template("income.html")


# ==============================
# ADD EXPENSE
# ==============================
@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form["amount"]
        description = request.form["description"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO expenses (user_id, amount, description) VALUES (%s, %s, %s)",
            (session["user_id"], amount, description),
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Expense added successfully")
        return redirect(url_for("dashboard"))

    return render_template("expenses.html")


# ==============================
# FORGOT PASSWORD
# ==============================
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        new_password = request.form["new_password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new_password, username),
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Password updated successfully")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


# ==============================
# CHANGE PASSWORD
# ==============================
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password=%s WHERE id=%s",
            (new_password, session["user_id"]),
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Password changed successfully")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")
    # ==============================
# VIEW RECORDS
# ==============================
@app.route("/view_records")
def view_records():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, amount, description FROM income WHERE user_id=%s", (session["user_id"],))
    incomes = cur.fetchall()

    cur.execute("SELECT id, amount, description FROM expenses WHERE user_id=%s", (session["user_id"],))
    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view_records.html", incomes=incomes, expenses=expenses)


    # ==============================
# SUMMARY
# ==============================
@app.route("/summary")
def summary():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Total Income
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=%s",
        (session["user_id"],)
    )
    total_income = cur.fetchone()[0]

    # Total Expenses
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s",
        (session["user_id"],)
    )
    total_expense = cur.fetchone()[0]

    balance = total_income - total_expense

    cur.close()
    conn.close()

    return render_template(
        "summary.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        profit=balance   # 👈 THIS FIXES ERROR
    )

@app.route("/edit_income/<int:id>", methods=["POST"])
def edit_income(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    amount = request.form["amount"]
    description = request.form["description"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE income SET amount=%s, description=%s WHERE id=%s AND user_id=%s",
        (amount, description, id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Income updated successfully")
    return redirect(url_for("view_records"))
    @app.route("/delete_income/<int:id>")
def delete_income(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM income WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Income deleted successfully")
    return redirect(url_for("view_records"))
    @app.route("/edit_expense/<int:id>", methods=["POST"])
def edit_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    amount = request.form["amount"]
    description = request.form["description"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE expenses SET amount=%s, description=%s WHERE id=%s AND user_id=%s",
        (amount, description, id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Expense updated successfully")
    return redirect(url_for("view_records"))
    @app.route("/delete_expense/<int:id>")
def delete_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Expense deleted successfully")
    return redirect(url_for("view_records"))










# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
