import sqlite3
import os
import time

class HistoryStore:
    def __init__(self, db_path="guardian_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                timestamp REAL NOT NULL,
                mode TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_location(self, lat, lng, mode):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO location_history (lat, lng, timestamp, mode) VALUES (?, ?, ?, ?)",
            (lat, lng, time.time(), mode)
        )
        conn.commit()
        conn.close()

    def get_all_history(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT lat, lng, timestamp FROM location_history")
        data = cursor.fetchall()
        conn.close()
        return data

    def get_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM location_history")
        count = cursor.fetchone()[0]
        conn.close()
        return count
