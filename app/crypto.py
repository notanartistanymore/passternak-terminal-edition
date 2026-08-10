from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet


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
