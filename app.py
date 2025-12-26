from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from models.db import get_db_connection
import functools
import io

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "eleven_stationery_secret"


# ================= LOGIN REQUIRED =================

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ================= AUTH =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))

        flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================= CHANGE PASSWORD =================

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (session["user"], old)
        ).fetchone()

        if not user:
            flash("Old password incorrect")
            conn.close()
            return redirect(url_for("change_password"))

        conn.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new, session["user"])
        )
        conn.commit()
        conn.close()

        flash("Password updated")
        return redirect(url_for("index"))

    return render_template("change_password.html")


# ================= FORGOT / RESET PASSWORD =================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        session["reset_user"] = request.form["username"]
        return redirect(url_for("reset_password"))
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new = request.form["new_password"]
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new, session["reset_user"])
        )
        conn.commit()
        conn.close()

        session.pop("reset_user")
        flash("Password reset successful")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


# ================= DASHBOARD =================

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
        conn.execute(
            "INSERT INTO income (date, amount, description) VALUES (%s,%s,%s)",
            (request.form["date"], request.form["amount"], request.form["description"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    return render_template("income.html")


@app.route("/edit/income/<int:id>", methods=["GET", "POST"])
@login_required
def edit_income(id):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM income WHERE id=%s", (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE income SET date=%s, amount=%s, description=%s WHERE id=%s",
            (
                request.form["date"],
                request.form["amount"],
                request.form["description"],
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    conn.close()
    return render_template("income.html", record=record, edit=True)


# ================= EXPENSE =================

@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (date, amount, purpose) VALUES (%s,%s,%s)",
            (request.form["date"], request.form["amount"], request.form["purpose"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    return render_template("expense.html")


@app.route("/edit/expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM expenses WHERE id=%s", (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE expenses SET date=%s, amount=%s, purpose=%s WHERE id=%s",
            (
                request.form["date"],
                request.form["amount"],
                request.form["purpose"],
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for("records"))

    conn.close()
    return render_template("expense.html", record=record, edit=True)


# ================= RECORDS =================

@app.route("/records")
@login_required
def records():
    conn = get_db_connection()
    incomes = conn.execute("SELECT * FROM income ORDER BY date DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()

    return render_template(
        "view_records.html",
        incomes=incomes,
        expenses=expenses
    )


# ================= SUMMARY =================

@app.route("/summary")
@login_required
def summary():
    conn = get_db_connection()
    income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income").fetchone()[0]
    expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
    conn.close()

    return render_template(
        "summary.html",
        income=income,
        expense=expense,
        profit=income - expense
    )


# ================= EXPORTS =================

@app.route("/export/income")
@login_required
def export_income():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT date, amount, description FROM income ORDER BY date"
    ).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Amount", "Description"])
    for r in rows:
        ws.append([r["date"], r["amount"], r["description"]])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="income.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/export/expenses")
@login_required
def export_expenses():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT date, amount, purpose FROM expenses ORDER BY date"
    ).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Amount", "Purpose"])
    for r in rows:
        ws.append([r["date"], r["amount"], r["purpose"]])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="expenses.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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
    pdf.drawString(50, 800, "Stationery Shop – Financial Summary")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Total Income  : ₹ {income}")
    pdf.drawString(50, 730, f"Total Expense : ₹ {expense}")
    pdf.drawString(50, 700, f"Profit        : ₹ {income - expense}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="summary.pdf",
        mimetype="application/pdf"
    )


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
