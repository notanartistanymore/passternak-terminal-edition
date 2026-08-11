from cryptography.fernet import InvalidToken

import sqlite3
import os

from storage import DATABASE
from crypto import decrypt_password, encrypt_password
from config import generate_password, Config

def authenticate() -> bytes | None:
    max_attempts = 3
    for attempt in range(max_attempts):
        master_password = input("Enter your master password: ").encode("utf-8")
        if check_master_password(master_password):
            return master_password
        print(f"Wrong password! {max_attempts - attempt - 1} attempts left.")
    return None


def check_master_password(master_password: bytes) -> bool:
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT password, salt FROM keyholder LIMIT 1")
        row = cursor.fetchone()

    if row is None:
        return True

    encrypted_password, salt = row
    try:
        decrypt_password(master_password, encrypted_password, salt)
        return True
    except InvalidToken:
        return False


def change_master_password(master_password: bytes) -> bytes:
    new_master_password = input("Enter new master password: ").encode(encoding="utf-8")
    check_new_master_password = input("Enter new master password one more time: ").encode(encoding="utf-8")
    if new_master_password != check_new_master_password:
        print("Passwords are different!")
        return master_password

    with sqlite3.connect(DATABASE) as db:
        try:
            with db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM keyholder")

                for row in cursor:
                    _, title, login, password, salt = row
                    decrypted = decrypt_password(master_password=master_password, encrypted_password=password, salt=salt)
                    encrypted = encrypt_password(master_password=new_master_password, password=decrypted, salt=salt)
                    cursor.execute("UPDATE keyholder SET password = ? WHERE title = ?", (encrypted, title))

                print("Master password successfully changed!")
        except sqlite3.Error as e:
            print(f"Error: {e}. Nothing changed.")

    return new_master_password


def create_item(config: Config, master_password: bytes):
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()

        temp_password = generate_password(config=config)
        temp_salt = os.urandom(16)
        encrypted_password = encrypt_password(master_password, temp_password, temp_salt)

        title = None
        while not title:
            title = input("Enter title: ").strip()

        cursor.execute("SELECT * FROM keyholder WHERE title = ?", (title,))
        data = cursor.fetchone()
        if not data:
            login = None
            while not login:
                login = input("Enter login: ").strip()
            cursor.execute(
                "INSERT INTO keyholder (title, login, password, salt) VALUES(?, ?, ?, ?)",
                (title, login, encrypted_password, temp_salt),
            )
            print(f"Login: {login} | Password: {temp_password}\n'{title}' was created!")
        else:
            overwrite_choice = None
            while overwrite_choice not in ("yes", "no"):
                overwrite_choice = input(
                    f"'{title}' already exists! Do you want to overwrite? (Yes, No): "
                ).lower()
                if overwrite_choice == "yes":
                    cursor.execute(
                        "UPDATE keyholder SET password = ?, salt = ? WHERE title = ?",
                        (encrypted_password, temp_salt, title),
                    )
                    print(f"Password '{temp_password}' for '{title}' was changed!")
                elif overwrite_choice == "no":
                    print("Nothing changed!")


def show_items(master_password: bytes):
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM keyholder")
        data = cursor.fetchall()

    for _, title, login, encrypted_password, salt in data:
        decrypted = decrypt_password(master_password, encrypted_password, salt)
        print(f"{title}\n--- Login: {login}\n--- Password: {decrypted}")


def rename_item():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM keyholder")
        for item in cursor:
            print(f"Name: {item[1]}.")

        rename_choice = input("What do you want to rename: ").strip()
        cursor.execute("SELECT title FROM keyholder WHERE title = ?", (rename_choice,))
        data = cursor.fetchone()
        if data:
            new_name_choice = input(f"New name for {rename_choice}: ").strip()
            cursor.execute("SELECT title FROM keyholder WHERE title = ?", (new_name_choice,))
            data = cursor.fetchone()
            if not data:
                cursor.execute(
                    "UPDATE keyholder SET title = ? WHERE title = ?", (new_name_choice, rename_choice)
                )
                print(f"You renamed '{rename_choice}' to '{new_name_choice}'")
            else:
                print("This name already exists!")
        else:
            print(f"Can't find '{rename_choice}' in database!")


def delete_item() -> None:
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM keyholder")
        for item in cursor:
            print(f"Name: {item[1]}.")

        delete_choice = input("What do you want to delete: ").strip()
        if not delete_choice:
            print("Name cannot be empty!")
            return

        cursor.execute("DELETE FROM keyholder WHERE title = ?", (delete_choice,))

        if cursor.rowcount:
            print(f"{delete_choice} deleted!")
        else:
            print(f"Can't find {delete_choice} in database!")
