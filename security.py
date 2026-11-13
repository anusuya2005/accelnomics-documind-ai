import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password):
    return _hasher.hash(password)


def verify_password(stored_hash, password):
    try:
        return _hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):    # wrong password or damaged hash
        return False


# Used when the username does not exist, so the check takes the same time either way.
DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def new_token():
    token = secrets.token_urlsafe(32)                # 32 random bytes: cannot be guessed
    return token, hash_token(token)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
