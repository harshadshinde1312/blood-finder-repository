from flask import Flask, render_template, request
import sqlite3
import math

app = Flask(__name__)


# ==============================
# DATABASE
# ==============================

def create_database():

    conn = sqlite3.connect("blood_finder.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            location TEXT NOT NULL,
            phone TEXT NOT NULL,
            available TEXT NOT NULL,
            latitude REAL,
            longitude REAL
        )
    """)

    conn.commit()
    conn.close()


create_database()


# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


# ==============================
# SEARCH BLOOD
# ==============================

@app.route("/search", methods=["GET", "POST"])
def search():

    if request.method == "POST":

        blood_group = request.form["blood_group"]
        location = request.form.get("location", "")

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        conn = sqlite3.connect("blood_finder.db")
        conn.row_factory = sqlite3.Row

        # --------------------------------
        # GPS SEARCH
        # --------------------------------

        if latitude and longitude:

            user_lat = float(latitude)
            user_lon = float(longitude)

            donors = conn.execute("""
                SELECT * FROM donors
                WHERE blood_group = ?
                AND available = 'Yes'
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
            """, (blood_group,)).fetchall()

            nearby_donors = []

            for donor in donors:

                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    donor["latitude"],
                    donor["longitude"]
                )

                donor_data = dict(donor)

                donor_data["distance"] = round(distance, 1)

                nearby_donors.append(donor_data)

            nearby_donors.sort(key=lambda x: x["distance"])

            conn.close()

            return render_template(
                "results.html",
                donors=nearby_donors,
                gps_search=True
            )

        # --------------------------------
        # MANUAL LOCATION SEARCH
        # --------------------------------

        donors = conn.execute("""
            SELECT * FROM donors
            WHERE blood_group = ?
            AND location LIKE ?
            AND available = 'Yes'
        """, (blood_group, "%" + location + "%")).fetchall()

        conn.close()

        return render_template(
            "results.html",
            donors=donors,
            gps_search=False
        )

    return render_template("search.html")


# ==============================
# DISTANCE CALCULATION
# ==============================

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ==============================
# DONOR REGISTRATION
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        blood_group = request.form["blood_group"]
        location = request.form["location"]
        phone = request.form["phone"]
        available = request.form["available"]

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        conn = sqlite3.connect("blood_finder.db")

        conn.execute("""
            INSERT INTO donors
            (name, blood_group, location, phone, available, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            blood_group,
            location,
            phone,
            available,
            latitude if latitude else None,
            longitude if longitude else None
        ))

        conn.commit()
        conn.close()

        return "Donor registered successfully! ❤️"

    return render_template("register.html")


# ==============================
# ABOUT
# ==============================

@app.route("/about")
def about():
    return render_template("about.html")


# ==============================
# START SERVER
# ==============================

if __name__ == "__main__":

    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

    