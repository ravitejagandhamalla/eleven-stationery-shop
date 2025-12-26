import os
import sqlite3
import io
from functools import wraps
from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    flash, send_file
)
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "eleven_stationery_secret"

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

# ================= AUTH =================

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("login"))

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
        flash("Invalid credentials")

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
        new = request.form["new_password"]
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new, session["user"])
        )
        conn.commit()
        conn.close()
        flash("Password updated")
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
        new = request.form["new_password"]
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new, session["reset_user"])
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

    rows = conn.execute("SELECT * FROM income").fetchall()
    conn.close()
    return render_template("income.html", rows=rows)

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

    rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return render_template("expense.html", rows=rows)

# ================= RECORDS =================

@app.route("/records")
@login_required
def records():
    conn = get_db_connection()
    income = conn.execute("SELECT * FROM income").fetchall()
    expense = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return render_template("view_records.html", income=income, expense=expense)

# ================= EXPORT EXCEL =================

@app.route("/export/income")
@login_required
def export_income():
    conn = get_db_connection()
    rows = conn.execute("SELECT date, amount, description FROM income").fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Amount", "Description"])
    for r in rows:
        ws.append([r["date"], r["amount"], r["description"]])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(stream, as_attachment=True, download_name="income.xlsx")

@app.route("/export/expenses")
@login_required
def export_expenses():
    conn = get_db_connection()
    rows = conn.execute("SELECT date, amount, purpose FROM expenses").fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Amount", "Purpose"])
    for r in rows:
        ws.append([r["date"], r["amount"], r["purpose"]])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(stream, as_attachment=True, download_name="expenses.xlsx")

# ================= EXPORT PDF =================

@app.route("/export/summary/pdf")
@login_required
def export_summary_pdf():
    conn = get_db_connection()
    income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
    expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "Stationery Shop Summary")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Total Income : ₹ {income}")
    pdf.drawString(50, 730, f"Total Expense: ₹ {expense}")
    pdf.drawString(50, 700, f"Profit       : ₹ {income - expense}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="summary.pdf")

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
