import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ==============================
# DATABASE CONNECTION
# ==============================
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(database_url)


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

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")

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

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=%s", (session["user_id"],))
    total_income = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s", (session["user_id"],))
    total_expenses = cur.fetchone()[0]

    balance = total_income - total_expenses

    cur.close()
    conn.close()

    return render_template("dashboard.html",
                           total_income=total_income,
                           total_expenses=total_expenses,
                           balance=balance,
                           username=session["username"])


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
            "INSERT INTO income (user_id, amount, description) VALUES (%s,%s,%s)",
            (session["user_id"], amount, description)
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
            "INSERT INTO expenses (user_id, amount, description) VALUES (%s,%s,%s)",
            (session["user_id"], amount, description)
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Expense added successfully")
        return redirect(url_for("dashboard"))

    return render_template("expenses.html")


# ==============================
# VIEW RECORDS
# ==============================
@app.route("/view_records")
def view_records():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, amount, description FROM income WHERE user_id=%s",
                (session["user_id"],))
    incomes = cur.fetchall()

    cur.execute("SELECT id, amount, description FROM expenses WHERE user_id=%s",
                (session["user_id"],))
    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view_records.html",
                           incomes=incomes,
                           expenses=expenses)


# ==============================
# EDIT INCOME
# ==============================
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


# ==============================
# DELETE INCOME
# ==============================
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


# ==============================
# EDIT EXPENSE
# ==============================
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


# ==============================
# DELETE EXPENSE
# ==============================
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
# SUMMARY
# ==============================
@app.route("/summary")
def summary():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=%s",
                (session["user_id"],))
    total_income = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s",
                (session["user_id"],))
    total_expenses = cur.fetchone()[0]

    balance = total_income - total_expenses

    cur.close()
    conn.close()

    return render_template("summary.html",
                           total_income=total_income,
                           total_expenses=total_expenses,
                           balance=balance)
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
            (new_password, session["user_id"])
        )

        conn.commit()
        cur.close()
        conn.close()

        flash("Password changed successfully")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")



# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)

