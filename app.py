import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-123")


# ==============================
# DATABASE CONNECTION
# ==============================
import os
import psycopg2

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return None

    try:
        conn = psycopg2.connect(database_url, sslmode="require")
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None

# ==============================
# HOME
# ==============================
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db_connection()

        if conn is None:
            return "Database connection error"

        cur = conn.cursor()

        email = request.form["email"]
        password = request.form["password"]

        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (email, password))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect(url_for("index"))
        else:
            return "Invalid credentials"

    return render_template("login.html")



# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==============================
# FORGOT PASSWORD
# ==============================
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]

        conn = get_db_connection()
        if conn is None:
            return "Database connection error"

        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new_password, email),
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


# ==============================
# CHANGE PASSWORD
# ==============================
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = get_db_connection()
        if conn is None:
            return "Database connection error"

        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new_password, session["user"]),
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("index"))

    return render_template("change_password.html")


# ==============================
# INCOME ROUTE (Fixes Your Error)
# ==============================
@app.route("/income")
def income():
    if "user" not in session:
        return redirect(url_for("login"))
    return "Income Page (You can build this later)"


# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
