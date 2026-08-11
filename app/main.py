from storage import initialize_database, DATABASE
from vault import authenticate, create_item, show_items, rename_item, delete_item, change_master_password
from config import Config, generate_password
from settings import change_settings
from backup import export_database, backup_database


def main():
    initialize_database(DATABASE)

    master_password = authenticate()
    if master_password is None:
        print("Too many failed attempts. Goodbye!")
        return

    config = Config(length=12, has_lowercase=True, has_uppercase=True, has_numbers=True, has_special=True)

    select = None
    while select != "EXIT":
        select = input("""
+===================================+
|               MENU                |                    
|-----------------------------------+
|   [1] GENERATE PASSWORD           |
|   [2] SAVE PASSWORD               |
|   [3] SHOW ALL PASSWORDS          |
|   [4] SETTINGS                    |
|   [5] RENAME ENTRY                |
|   [6] DELETE ENTRY                |
|   [7] CHANGE MASTER PASSWORD      |
|   [8] EXPORT DATABASE             |
|-----------------------------------|
|   [0] EXIT                        |
+===================================+
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
            master_password = change_master_password(master_password)

        elif select == "8":
            file_name = None
            while not file_name:
                file_name = input("Enter file name: ").strip()
            export_database(master_password, file_name)

        elif select == "0":
            backup_database()
            select = "EXIT"

        else:
            print("Error! Choose right menu item!")

    print("Goodbye!")


if __name__ == "__main__":
    main()
