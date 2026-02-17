import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ==============================
# DATABASE CONNECTION
# ==============================
def get_db_connection():
    database_url = os.environ.get("postgresql://ravi_teja_user:8OVmBnpToXXuq3qAiL9SmMof3AYD8NvO@dpg-d69va7vpm1nc739obqa0-a.virginia-postgres.render.com:5432/ravi_teja")

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

    return render_template("dashboard.html")


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
# MAIN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
