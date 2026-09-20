import os
import sqlite3
from datetime import datetime

from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "teburio.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            people INTEGER NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()
    db.close()


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None
        if not name or not email or not password:
            error = "Bitte alle Felder ausfüllen."
        elif len(password) < 6:
            error = "Das Passwort muss mindestens 6 Zeichen lang sein."

        if error is None:
            db = get_db()
            existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing is not None:
                error = "Diese E-Mail-Adresse ist bereits registriert."

        if error is None:
            db = get_db()
            db.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), datetime.utcnow().isoformat()),
            )
            db.commit()
            return redirect(url_for("login", registered=1))

        return render_template("register.html", error=error, name=name, email=email)

    return render_template("register.html", error=None, name="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="E-Mail oder Passwort ist falsch.", email=email)

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("reservations"))

    registered = request.args.get("registered")
    return render_template("login.html", error=None, email="", registered=registered)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/reservierung", methods=["GET", "POST"])
def reservations():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    db = get_db()
    error = None

    if request.method == "POST":
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()
        people = request.form.get("people", "").strip()
        note = request.form.get("note", "").strip()

        if not date or not time or not people:
            error = "Bitte Datum, Uhrzeit und Personenanzahl angeben."
        else:
            try:
                people_int = int(people)
                if people_int < 1:
                    raise ValueError
            except ValueError:
                error = "Die Personenanzahl muss eine positive Zahl sein."

        if error is None:
            db.execute(
                "INSERT INTO reservations (user_id, date, time, people, note, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user["id"], date, time, people_int, note, datetime.utcnow().isoformat()),
            )
            db.commit()
            return redirect(url_for("reservations"))

    my_reservations = db.execute(
        "SELECT * FROM reservations WHERE user_id = ? ORDER BY date, time",
        (user["id"],),
    ).fetchall()

    return render_template("reservations.html", reservations=my_reservations, error=error)


@app.route("/reservierung/<int:reservation_id>/loeschen", methods=["POST"])
def delete_reservation(reservation_id):
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM reservations WHERE id = ? AND user_id = ?",
        (reservation_id, user["id"]),
    )
    db.commit()
    return redirect(url_for("reservations"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
