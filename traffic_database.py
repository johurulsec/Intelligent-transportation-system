import os
import sqlite3


class CaptureDatabase:
    def __init__(self, database_path):
        self.database_path = database_path
        parent_dir = os.path.dirname(database_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    def log_capture(self, vehicle_type, image_path, captured_at):
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            table_name = self._quote_identifier(vehicle_type)
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_type TEXT NOT NULL,
                    image_name TEXT NOT NULL,
                    image_path TEXT NOT NULL UNIQUE,
                    captured_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {table_name}
                (vehicle_type, image_name, image_path, captured_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    vehicle_type,
                    os.path.basename(image_path),
                    image_path,
                    captured_at,
                ),
            )
            connection.commit()

    @staticmethod
    def _quote_identifier(name):
        return '"' + name.replace('"', '""') + '"'
