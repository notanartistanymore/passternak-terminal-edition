from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet, InvalidToken

import os
import sqlite3
from secrets import choice, SystemRandom


DATABASE = "database.db"


# --- Шифрование ---

def derive_key(master_password: bytes, salt: bytes) -> bytes:
    """Превращает мастер-пароль + соль в 32-байтный ключ, пригодный для Fernet.
    Вынесено в отдельную функцию, чтобы не дублировать KDF-настройки
    в encrypt_password и decrypt_password (единый источник правды)."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    return urlsafe_b64encode(kdf.derive(master_password))


def encrypt_password(master_password: bytes, password: str, salt: bytes) -> bytes:
    key = derive_key(master_password, salt)
    return Fernet(key).encrypt(password.encode("utf-8"))


def decrypt_password(master_password: bytes, encrypted_password: bytes, salt: bytes) -> str:
    key = derive_key(master_password, salt)
    return Fernet(key).decrypt(encrypted_password).decode("utf-8")


def check_master_password(master_password: bytes) -> bool:
    """Проверяет, подходит ли введённый мастер-пароль к уже сохранённым данным.

    Если записей в базе ещё нет (первый запуск) — проверять не с чем,
    любой введённый пароль становится "тем самым" мастер-паролем.
    Если записи есть — пробуем расшифровать одну из них; Fernet сам
    выбросит InvalidToken, если ключ (то есть пароль) неверный.
    """
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT password, salt FROM keyholder LIMIT 1")
        row = cursor.fetchone()

    if row is None:
        return True  # первый запуск, база пустая

    encrypted_password, salt = row
    try:
        decrypt_password(master_password, encrypted_password, salt)
        return True
    except InvalidToken:
        return False


# --- Генератор паролей ---

class Config:
    def __init__(self, length, has_lowercase, has_uppercase, has_numbers, has_special):
        self.length: int = length
        self.max_pass_length = 24

        self.has_lowercase: bool = has_lowercase
        self.has_uppercase: bool = has_uppercase
        self.has_numbers: bool = has_numbers
        self.has_special: bool = has_special

    def categories(self):
        return {
            "lowercase": (self.has_lowercase, "abcdefghijklmnopqrstuvwxyz"),
            "uppercase": (self.has_uppercase, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "numbers": (self.has_numbers, "0123456789"),
            "special": (self.has_special, "!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~"),
        }


def generate_password(config: Config) -> str:
    enabled_categories = [symbols for flag, symbols in config.categories().values() if flag]
    if not enabled_categories:
        raise ValueError("Turn on at least one category!")
    if config.length < len(enabled_categories):
        raise ValueError("Password length cannot be less than the number of enabled categories!")

    # Сначала гарантируем хотя бы один символ из каждой включённой категории
    password = [choice(symbols) for symbols in enabled_categories]
    all_symbols = "".join(enabled_categories)

    # Остальные символы — из общего пула
    for _ in range(config.length - len(enabled_categories)):
        password.append(choice(all_symbols))

    SystemRandom().shuffle(password)

    return "".join(password)


# --- База данных ---

def initialize_database(database: str) -> None:
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyholder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                password BLOB NOT NULL,
                salt BLOB NOT NULL
            )
        """)


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
            cursor.execute(
                "INSERT INTO keyholder (title, password, salt) VALUES(?, ?, ?)",
                (title, encrypted_password, temp_salt),
            )
            print(f"Password '{temp_password}' for '{title}' was created!")
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

    for _, title, encrypted_password, salt in data:
        decrypted = decrypt_password(master_password, encrypted_password, salt)
        print(f"{title}: {decrypted}")


def rename_item():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM keyholder")
        data = cursor.fetchall()
        for item in data:
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
        data = cursor.fetchall()
        for item in data:
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


def change_settings(config: Config):
    setting_choice = None
    while setting_choice != "back":
        setting_choice = input(f"""
--- Settings ---
1. Choose amount of symbols (Current: {config.length})
2. {"Disable" if config.has_lowercase else "Enable"} lowercase (Current: {config.has_lowercase})
3. {"Disable" if config.has_uppercase else "Enable"} uppercase (Current: {config.has_uppercase})
4. {"Disable" if config.has_numbers else "Enable"} numbers (Current: {config.has_numbers})
5. {"Disable" if config.has_special else "Enable"} special symbols (Current: {config.has_special})
6. Back
----------------
        """)

        if setting_choice == "1":
            try:
                new_length = int(input("New length is: "))
                min_pass_length = len([flag for flag, _ in config.categories().values() if flag])
                if min_pass_length <= new_length <= config.max_pass_length:
                    config.length = new_length
                else:
                    print(f"Min symbols: {min_pass_length}. Max symbols: {config.max_pass_length}")
            except ValueError:
                print("Only numeric is available!")

        elif setting_choice == "2":
            config.has_lowercase = not config.has_lowercase
        elif setting_choice == "3":
            config.has_uppercase = not config.has_uppercase
        elif setting_choice == "4":
            config.has_numbers = not config.has_numbers
        elif setting_choice == "5":
            config.has_special = not config.has_special
        elif setting_choice == "6":
            setting_choice = "back"
        else:
            print("Error! Choose right menu item!")


def authenticate() -> bytes | None:
    """Спрашивает мастер-пароль. Если база пустая — задаёт новый мастер-пароль.
    Если в базе уже есть записи — даёт до 3 попыток ввести правильный пароль."""
    max_attempts = 3
    for attempt in range(max_attempts):
        master_password = input("Enter your master password: ").encode("utf-8")
        if check_master_password(master_password):
            return master_password
        print(f"Wrong password! {max_attempts - attempt - 1} attempts left.")
    return None


def main():
    initialize_database(DATABASE)

    master_password = authenticate()
    if master_password is None:
        print("Too many failed attempts. Goodbye!")
        return

    config = Config(length=12, has_lowercase=True, has_uppercase=True, has_numbers=True, has_special=True)

    select = None
    while select != "exit":
        select = input("""
--- Menu ---
1. Generate new password
2. Create new item in database
3. Show all items
4. Settings
5. Rename item in database
6. Delete item in database
7. Exit
------------
        """)

        if select == "1":
            try:
                temp_password = generate_password(config=config)
                print(f"Password: {temp_password}")
            except ValueError as e:
                print(f"Error: {e}")

        elif select == "2":
            try:
                create_item(config, master_password)
            except ValueError as e:
                print(f"Error: {e}")

        elif select == "3":
            show_items(master_password)

        elif select == "4":
            change_settings(config)

        elif select == "5":
            rename_item()

        elif select == "6":
            delete_item()

        elif select == "7":
            select = "exit"

        else:
            print("Error! Choose right menu item!")

    print("Goodbye!")


if __name__ == "__main__":
    main()