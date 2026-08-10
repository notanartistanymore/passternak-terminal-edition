import sqlite3
import json
import os
from datetime import datetime
from base64 import b64encode

from storage import DATABASE
from crypto import decrypt_password


def export_database(master_password: bytes, file_name: str) -> None:
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT title, login, password, salt FROM keyholder")
        export_data = []
        for row in cursor:
            title, login, encrypted_password, salt = row
            decrypted_password = decrypt_password(master_password, encrypted_password, salt)
            export_data.append({
                "title": title,
                "login": login,
                "password": decrypted_password
            })

        with open(f"{file_name}.json", "w", encoding="utf-8") as file:
            json.dump(export_data, file, ensure_ascii=False, indent=4)
            print("Database was successfully exported!")


def backup_database() -> None:
    source_dir = os.path.dirname(os.path.abspath(__file__))
    backup_path = os.path.join(source_dir, "backup")
    os.makedirs(backup_path, exist_ok=True)
    created_at = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_path = os.path.join(backup_path, f"{created_at}.json")

    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM keyholder")
        backup_data = []
        for row in cursor:
            _, title, login, password, salt = row
            backup_data.append({
                "title": title,
                "login": login,
                "password": b64encode(password).decode("utf-8"),
                "salt": b64encode(salt).decode("utf-8")
            })

        with open(file_path, "w") as file:
                json.dump(backup_data, file, ensure_ascii=False, indent=4)
