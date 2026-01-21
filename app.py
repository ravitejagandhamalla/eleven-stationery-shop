import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-123")


def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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
            return redirect(url_for("index"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
