import math
import sqlite3
from pathlib import Path
import os
from werkzeug.utils import secure_filename

from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = "namma-yantra-share-demo-key"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

BANGALORE_AREAS = {
    "Whitefield": (12.9698, 77.7500),
    "KR Puram": (13.0075, 77.6959),
    "Marathahalli": (12.9591, 77.6974),
    "Hoskote": (13.0707, 77.7981),
    "Yelahanka": (13.1007, 77.5963),
    "Hebbal": (13.0358, 77.5970),
    "Devanahalli": (13.2466, 77.7118),
    "Chikkabanavara": (13.0845, 77.5006),
    "Electronic City": (12.8452, 77.6602),
    "BTM Layout": (12.9166, 77.6101),
    "Jayanagar": (12.9250, 77.5938),
    "Banashankari": (12.9255, 77.5468),
    "Rajajinagar": (12.9915, 77.5544),
    "Yeshwanthpur": (13.0223, 77.5500),
    "Nelamangala": (13.1028, 77.3936),
    "Vijayanagar": (12.9719, 77.5316),
    "MG Road": (12.9758, 77.6050),
    "Indiranagar": (12.9784, 77.6408),
    "Koramangala": (12.9352, 77.6245)
}

CONDITIONS = ["Excellent", "Good", "Average", "Needs minor repair"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile TEXT UNIQUE NOT NULL,
                name TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                price_per_day REAL NOT NULL,
                location TEXT NOT NULL,
                condition TEXT NOT NULL,
                delivery INTEGER NOT NULL DEFAULT 0,
                pickup INTEGER NOT NULL DEFAULT 0,
                images TEXT,
                available INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                days INTEGER NOT NULL,
                selected_dates TEXT NOT NULL,
                service_mode TEXT NOT NULL,
                total_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(machine_id) REFERENCES machines(id),
                FOREIGN KEY(customer_id) REFERENCES users(id)
            )
            """
        )
        migrate_db(conn)


def migrate_db(conn):
    machine_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(machines)").fetchall()
    }
    if "price_per_day" not in machine_columns:
        conn.execute("ALTER TABLE machines ADD COLUMN price_per_day REAL DEFAULT 0")
        if "price_per_hour" in machine_columns:
            conn.execute("UPDATE machines SET price_per_day = price_per_hour")

    order_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
    }
    if "days" not in order_columns:
        conn.execute("ALTER TABLE orders ADD COLUMN days INTEGER DEFAULT 1")
        if "hours" in order_columns:
            conn.execute("UPDATE orders SET days = hours")
    if "selected_dates" not in order_columns:
        conn.execute("ALTER TABLE orders ADD COLUMN selected_dates TEXT DEFAULT ''")


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def booked_dates_for_machine(conn, machine_id):
    rows = conn.execute(
        "SELECT selected_dates FROM orders WHERE machine_id = ?", (machine_id,)
    ).fetchall()
    booked = set()
    for row in rows:
        dates = [date.strip() for date in row["selected_dates"].split(",")]
        booked.update(date for date in dates if date)
    return booked


def table_columns(conn, table_name):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}


@app.context_processor
def inject_globals():
    return {"user": current_user(), "areas": BANGALORE_AREAS.keys()}


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        otp = request.form.get("otp", "").strip()
        if len(mobile) < 4 or not mobile.isdigit():
            flash("Enter a valid mobile number.")
            return redirect(url_for("login"))
        if otp != mobile[-4:]:
            flash("Invalid OTP. Demo OTP is the last 4 digits of your mobile number.")
            return redirect(url_for("login"))

        with get_db() as conn:
            conn.execute("INSERT OR IGNORE INTO users (mobile) VALUES (?)", (mobile,))
            user = conn.execute("SELECT * FROM users WHERE mobile = ?", (mobile,)).fetchone()
        session["user_id"] = user["id"]
        flash("Login successful.")
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("home"))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user()

    if request.method == 'POST':
        name = request.form['name']

        with get_db() as conn:
            conn.execute(
                "UPDATE users SET name=? WHERE id=?",
                (name, user["id"])
            )

        return redirect(url_for('home'))

    return render_template('profile.html', user=user)


@app.route("/list", methods=["GET", "POST"])
@login_required
def list_machine():
    if request.method == "POST":
        photos = request.files.getlist("photos")

        saved_images = []

        for photo in photos:

            if photo.filename:

                filename = secure_filename(photo.filename)

                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                photo.save(path)

                saved_images.append(filename)

        images_string = ",".join(saved_images)

        delivery = 1 if request.form.get("delivery") else 0
        pickup = 1 if request.form.get("pickup") else 0
        if not delivery and not pickup:
            flash("Select at least one service option.")
            return redirect(url_for("list_machine"))

        with get_db() as conn:
            columns = table_columns(conn, "machines")
            price_per_day = float(request.form["price_per_day"])
            field_names = [
                "owner_id",
                "name",
                "company",
                "price_per_day",
                "location",
                "condition",
                "delivery",
                "pickup",
                "images",
            ]
            values = [
                session["user_id"],
                request.form["name"].strip(),
                request.form["company"].strip(),
                price_per_day,
                request.form["location"],
                request.form["condition"],
                delivery,
                pickup,
                images_string,
            ]
            if "price_per_hour" in columns:
                field_names.append("price_per_hour")
                values.append(price_per_day)
            placeholders = ", ".join("?" for _ in field_names)
            conn.execute(
                f"INSERT INTO machines ({', '.join(field_names)}) VALUES ({placeholders})",
                values,
            )
        flash("Machine listed successfully.")
        return redirect(url_for("my_machines"))
    return render_template("list.html", conditions=CONDITIONS)


@app.route("/browse")
@login_required
def browse():
    sort = request.args.get("sort", "distance")
    user_lat = request.args.get("lat", type=float)
    user_lon = request.args.get("lon", type=float)
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT machines.*, users.mobile AS owner_mobile
            FROM machines
            JOIN users ON users.id = machines.owner_id
            WHERE machines.available = 1 AND machines.owner_id != ?
            """,
            (session["user_id"],),
        ).fetchall()

    machines = []
    for row in rows:
        item = dict(row)
        area_lat, area_lon = BANGALORE_AREAS[item["location"]]
        item["lat"] = area_lat
        item["lon"] = area_lon
        item["distance"] = None
        if user_lat is not None and user_lon is not None:
            item["distance"] = haversine_km(user_lat, user_lon, area_lat, area_lon)
        machines.append(item)

    if sort == "price":
        machines.sort(key=lambda item: item["price_per_day"])
    elif user_lat is not None and user_lon is not None:
        machines.sort(key=lambda item: item["distance"])

    return render_template(
        "browse.html",
        machines=machines,
        sort=sort,
        has_live_location=user_lat is not None and user_lon is not None,
    )


@app.route("/my-machines")
@login_required
def my_machines():
    with get_db() as conn:
        machines = conn.execute(
            "SELECT * FROM machines WHERE owner_id = ? ORDER BY id DESC",
            (session["user_id"],),
        ).fetchall()
    return render_template("my_machines.html", machines=machines)


@app.route("/toggle/<int:machine_id>", methods=["POST"])
@login_required
def toggle_machine(machine_id):
    with get_db() as conn:
        machine = conn.execute(
            "SELECT * FROM machines WHERE id = ? AND owner_id = ?",
            (machine_id, session["user_id"]),
        ).fetchone()
        if machine:
            conn.execute(
                "UPDATE machines SET available = ? WHERE id = ?",
                (0 if machine["available"] else 1, machine_id),
            )
            flash("Availability updated.")
    return redirect(url_for("my_machines"))


@app.route("/request/<int:machine_id>", methods=["GET", "POST"])
@login_required
def request_machine(machine_id):
    with get_db() as conn:
        machine = conn.execute(
            "SELECT * FROM machines WHERE id = ? AND available = 1", (machine_id,)
        ).fetchone()
        booked_dates = booked_dates_for_machine(conn, machine_id)
    if not machine or machine["owner_id"] == session["user_id"]:
        flash("Machine is not available.")
        return redirect(url_for("browse"))

    available_modes = []
    if machine["delivery"]:
        available_modes.append("Delivery")
    if machine["pickup"]:
        available_modes.append("Pickup")

    if request.method == "POST":
        days = max(1, int(request.form["days"]))
        service_mode = request.form["service_mode"]
        selected_dates = [
            date.strip()
            for date in request.form.get("selected_dates", "").split(",")
            if date.strip()
        ]
        if service_mode not in available_modes:
            flash("Selected service mode is not available.")
            return redirect(url_for("request_machine", machine_id=machine_id))
        if len(selected_dates) != days or len(set(selected_dates)) != days:
            flash("Select exactly one calendar date for each requested day.")
            return redirect(url_for("request_machine", machine_id=machine_id))
        already_booked = sorted(set(selected_dates) & booked_dates)
        if already_booked:
            flash(f"Already booked for: {', '.join(already_booked)}.")
            return redirect(url_for("request_machine", machine_id=machine_id))
        total = days * machine["price_per_day"]
        with get_db() as conn:
            columns = table_columns(conn, "orders")
            field_names = [
                "machine_id",
                "customer_id",
                "days",
                "selected_dates",
                "service_mode",
                "total_price",
            ]
            values = [
                machine_id,
                session["user_id"],
                days,
                ",".join(sorted(selected_dates)),
                service_mode,
                total,
            ]
            if "hours" in columns:
                field_names.append("hours")
                values.append(days)
            placeholders = ", ".join("?" for _ in field_names)
            conn.execute(
                f"INSERT INTO orders ({', '.join(field_names)}) VALUES ({placeholders})",
                values,
            )
        flash("Order request placed successfully.")
        return redirect(url_for("orders"))

    return render_template(
        "request.html",
        machine=machine,
        available_modes=available_modes,
        booked_dates=sorted(booked_dates),
    )


@app.route("/orders")
@login_required
def orders():
    with get_db() as conn:
        owner_orders = conn.execute(
            """
            SELECT orders.*, machines.name AS machine_name, users.mobile AS customer_mobile
            FROM orders
            JOIN machines ON machines.id = orders.machine_id
            JOIN users ON users.id = orders.customer_id
            WHERE machines.owner_id = ?
            ORDER BY orders.created_at DESC
            """,
            (session["user_id"],),
        ).fetchall()
        customer_orders = conn.execute(
            """
            SELECT 
                orders.*, 
                machines.name AS machine_name, 
                machines.company AS company,
                users.mobile AS owner_mobile

            FROM orders

            JOIN machines ON machines.id = orders.machine_id
            JOIN users ON users.id = machines.owner_id

            WHERE orders.customer_id = ?

            ORDER BY orders.created_at DESC
            """,
            (session["user_id"],),
        ).fetchall()
    return render_template(
        "orders.html", owner_orders=owner_orders, customer_orders=customer_orders
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
