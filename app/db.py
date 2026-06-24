import sqlite3
from contextlib import contextmanager

DB_PATH = "readings.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_id TEXT NOT NULL,
    owner_name TEXT,
    lat REAL,
    lng REAL,
    timestamp TEXT NOT NULL,
    soil_n REAL,
    soil_p REAL,
    soil_k REAL,
    soil_ph REAL,
    air_temp_c REAL,
    humidity_pct REAL,
    rainfall_mm REAL,
    soil_moisture_pct REAL,
    predicted_crop TEXT,
    confidence REAL,
    filtered INTEGER
)
"""

SCHEMA_FARMS = """
CREATE TABLE IF NOT EXISTS farms (
    farm_id TEXT PRIMARY KEY,
    farm_name TEXT,
    owner_name TEXT,
    hectares REAL,
    polygon TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

SCHEMA_FARMERS = """
CREATE TABLE IF NOT EXISTS farmers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
)
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)
        conn.execute(SCHEMA_FARMS)
        conn.execute(SCHEMA_FARMERS)
        try:
            conn.execute("ALTER TABLE farms ADD COLUMN farm_name TEXT")
        except sqlite3.OperationalError:
            pass  # ponytail: already migrated on a prior run
        try:
            conn.execute("ALTER TABLE farms ADD COLUMN farmer_id TEXT REFERENCES farmers(id) ON DELETE SET NULL")
        except sqlite3.OperationalError:
            pass  # already migrated
        try:
            conn.execute("ALTER TABLE farmers ADD COLUMN password_hash TEXT")
        except sqlite3.OperationalError:
            pass  # already migrated
        try:
            conn.execute("ALTER TABLE farmers ADD COLUMN role TEXT DEFAULT 'farmer'")
        except sqlite3.OperationalError:
            pass  # already migrated


def insert_farm(farm: dict) -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO farms (farm_id, farm_name, owner_name, hectares, polygon, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (farm["farm_id"], farm["farm_name"], farm["owner_name"], farm["hectares"], farm["polygon"], farm["created_at"]),
        )
    return get_farm(farm["farm_id"])


def get_farm(farm_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farms WHERE farm_id = ?", (farm_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_farm_by_name(farm_name: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farms WHERE farm_name = ?", (farm_name,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_farms() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farms ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


def update_farm(farm_id: str, farm_name: str, owner_name: str | None, hectares: float, polygon: str) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE farms SET farm_name = ?, owner_name = ?, hectares = ?, polygon = ? WHERE farm_id = ?",
            (farm_name, owner_name, hectares, polygon, farm_id),
        )
    return get_farm(farm_id)


def delete_farm(farm_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM farms WHERE farm_id = ?", (farm_id,))
        conn.execute("DELETE FROM readings WHERE plot_id LIKE ?", (f"{farm_id}-%",))


def get_latest_for_farm(farm_id: str) -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT r.* FROM readings r
            INNER JOIN (
                SELECT plot_id, MAX(timestamp) AS max_ts FROM readings
                WHERE plot_id LIKE ? GROUP BY plot_id
            ) latest ON r.plot_id = latest.plot_id AND r.timestamp = latest.max_ts
            """,
            (f"{farm_id}-%",),
        )
        return [dict(r) for r in cur.fetchall()]


def insert_reading(row: dict) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO readings
                (plot_id, owner_name, lat, lng, timestamp, soil_n, soil_p, soil_k,
                 soil_ph, air_temp_c, humidity_pct, rainfall_mm, soil_moisture_pct,
                 predicted_crop, confidence, filtered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["plot_id"], row["owner_name"], row["lat"], row["lng"],
                row["timestamp"], row["soil_n"], row["soil_p"], row["soil_k"],
                row["soil_ph"], row["air_temp_c"], row["humidity_pct"],
                row["rainfall_mm"], row["soil_moisture_pct"],
                row["predicted_crop"], row["confidence"], int(row["filtered"]),
            ),
        )
        row_id = cur.lastrowid
    return get_reading_by_id(row_id)


def get_reading_by_id(row_id: int) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM readings WHERE id = ?", (row_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_readings() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM readings ORDER BY timestamp DESC")
        return [dict(r) for r in cur.fetchall()]


def get_readings_for_plot(plot_id: str) -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM readings WHERE plot_id = ? ORDER BY timestamp DESC",
            (plot_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_latest_per_plot() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT r.* FROM readings r
            INNER JOIN (
                SELECT plot_id, MAX(timestamp) AS max_ts
                FROM readings
                GROUP BY plot_id
            ) latest
            ON r.plot_id = latest.plot_id AND r.timestamp = latest.max_ts
            """
        )
        return [dict(r) for r in cur.fetchall()]


def insert_farmer(farmer: dict) -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO farmers (id, name, created_at, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (farmer["id"], farmer["name"], farmer["created_at"],
             farmer.get("password_hash"), farmer.get("role", "farmer")),
        )
    return get_farmer(farmer["id"])


def set_farmer_password(farmer_id: str, password_hash: str):
    with get_conn() as conn:
        conn.execute("UPDATE farmers SET password_hash = ? WHERE id = ?", (password_hash, farmer_id))


def get_farmer(farmer_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_farmer_by_name(name: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farmers WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_farmers() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT f.*, COUNT(fm.farm_id) AS farm_count
            FROM farmers f
            LEFT JOIN farms fm ON fm.farmer_id = f.id
            GROUP BY f.id
            ORDER BY f.created_at DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def update_farmer(farmer_id: str, name: str) -> dict | None:
    with get_conn() as conn:
        conn.execute("UPDATE farmers SET name = ? WHERE id = ?", (name, farmer_id))
    return get_farmer(farmer_id)


def delete_farmer(farmer_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE farms SET farmer_id = NULL WHERE farmer_id = ?", (farmer_id,))
        conn.execute("DELETE FROM farmers WHERE id = ?", (farmer_id,))


def assign_farm_to_farmer(farm_id: str, farmer_id: str | None):
    with get_conn() as conn:
        conn.execute("UPDATE farms SET farmer_id = ? WHERE farm_id = ?", (farmer_id, farm_id))
