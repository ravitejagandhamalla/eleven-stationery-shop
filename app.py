import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "785752cf9871d5a9418651dbfac41b3b"

# ================= DATABASE =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ================= LOGIN REQUIRED =================

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ================= HOME / INDEX =================

@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("login"))

@app.route("/index")
@login_required
def index():
    return redirect(url_for("dashboard"))

# ================= AUTH =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= PASSWORD =================

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_password, session["user"])
        )
        conn.commit()
        conn.close()

        flash("Password updated successfully")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        session["reset_user"] = request.form["username"]
        return redirect(url_for("reset_password"))
    return render_template("forgot_password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_password, session["reset_user"])
        )
        conn.commit()
        conn.close()

        session.pop("reset_user", None)
        flash("Password reset successful")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ================= DASHBOARD =================

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ================= INCOME =================

@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO income (date, amount, description) VALUES (?,?,?)",
            (request.form["date"], request.form["amount"], request.form["description"])
        )
        conn.commit()

    records = conn.execute("SELECT * FROM income ORDER BY date DESC").fetchall()
    conn.close()

    return render_template("income.html", records=records)

# ================= EXPENSE =================

@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (?,?,?)",
            (request.form["date"], request.form["amount"], request.form["purpose"])
        )
        conn.commit()

    records = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()

    return render_template("expense.html", records=records)

# ================= RECORDS =================

@app.route("/records")
@login_required
def records():
    conn = get_db_connection()
    income = conn.execute("SELECT * FROM income ORDER BY date DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()

    return render_template(
        "view_records.html",
        income=income,
        expenses=expenses
    )

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
