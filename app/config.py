from secrets import choice, SystemRandom


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

    password = [choice(symbols) for symbols in enabled_categories]
    all_symbols = "".join(enabled_categories)

    for _ in range(config.length - len(enabled_categories)):
        password.append(choice(all_symbols))

    SystemRandom().shuffle(password)

    return "".join(password)
