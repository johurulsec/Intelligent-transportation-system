import os
import sqlite3


class CaptureDatabase:
    def __init__(self, database_path):
        self.database_path = database_path
        parent_dir = os.path.dirname(database_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    def log_capture(self, saved_capture):
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            table_name = self._quote_identifier(saved_capture.vehicle_type)
            self._ensure_table(cursor, table_name)
            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {table_name}
                (vehicle_type, image_name, image_path, plate_image_name, plate_image_path, plate_text, plate_text_path, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_capture.vehicle_type,
                    saved_capture.vehicle_image_name,
                    saved_capture.vehicle_image_path,
                    saved_capture.plate_image_name,
                    saved_capture.plate_image_path,
                    saved_capture.plate_text,
                    saved_capture.plate_text_path,
                    saved_capture.captured_at,
                ),
            )
            connection.commit()

    def _ensure_table(self, cursor, table_name):
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_type TEXT NOT NULL,
                image_name TEXT NOT NULL,
                image_path TEXT NOT NULL UNIQUE,
                plate_image_name TEXT,
                plate_image_path TEXT,
                plate_text TEXT,
                plate_text_path TEXT,
                captured_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "plate_image_name": "TEXT",
            "plate_image_path": "TEXT",
            "plate_text": "TEXT",
            "plate_text_path": "TEXT",
            "captured_at": "TEXT",
        }

        for column_name, column_type in expected_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    @staticmethod
    def _quote_identifier(name):
        return '"' + name.replace('"', '""') + '"'
