from config import Config


def change_settings(config: Config):
    setting_choice = None
    while setting_choice != "back":
        setting_choice = input(f"""
--- Settings ---
[1] Choose amount of symbols (Current: {config.length})
[2] {"Disable" if config.has_lowercase else "Enable"} lowercase (Current: {config.has_lowercase})
[3] {"Disable" if config.has_uppercase else "Enable"} uppercase (Current: {config.has_uppercase})
[4] {"Disable" if config.has_numbers else "Enable"} numbers (Current: {config.has_numbers})
[5] {"Disable" if config.has_special else "Enable"} special symbols (Current: {config.has_special})
[6] Back
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
