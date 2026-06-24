"""Password hashing for farmer/admin accounts.

ponytail: stdlib pbkdf2 instead of adding bcrypt/passlib as a dependency —
plenty secure for a capstone demo with no real user data at stake.
"""
import hashlib
import hmac
import os

_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, _, hash_hex = stored.partition("$")
    if not hash_hex:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return hmac.compare_digest(dk.hex(), hash_hex)
