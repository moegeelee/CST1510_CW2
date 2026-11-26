"""Register and log in with bcrypt and a local user file.

Mohammed Mohammed Alhaji
Data Science | CST1510
Run with: python auth.py
"""

from contextlib import contextmanager
from getpass import getpass
from pathlib import Path
import sys

import bcrypt

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


USERS_FILE = Path(__file__).parent / "DATA" / "users.txt"
LOGIN_FAILED = "Wrong username or password."


@contextmanager
def _locked_users(file, shared=False):
    """Keep a user-file operation together on Windows, Mac and Linux."""
    windows = sys.platform == "win32"
    if windows:
        # Windows locks a byte range, including the first byte of an empty file.
        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
    else:
        mode = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
        fcntl.flock(file.fileno(), mode)
    try:
        yield
    finally:
        if windows:
            file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)


def generate_hash(password):
    """Return a salted bcrypt hash as text, without truncating the password."""
    if not isinstance(password, str):
        raise TypeError("Password must be text.")
    byte_password = password.encode("utf-8")
    if len(byte_password) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes.")
    return bcrypt.hashpw(byte_password, bcrypt.gensalt()).decode("utf-8")


def is_valid_hash(password, hashed):
    """Check a password safely, including damaged stored hashes."""
    if not isinstance(password, str) or not isinstance(hashed, str):
        return False
    try:
        byte_password = password.encode("utf-8")
        if len(byte_password) > 72:
            return False
        return bcrypt.checkpw(byte_password, hashed.encode("utf-8"))
    except ValueError:
        return False


def _read_users(file):
    """Read complete user rows, skipping blank or broken lines."""
    users = {}
    for line in file:
        name, separator, stored_hash = line.strip().partition(",")
        name = name.strip()
        if separator and name and stored_hash:
            # Keep the first row if an old file contains a duplicate name.
            users.setdefault(name.casefold(), stored_hash)
    return users


def user_exists(username, path=USERS_FILE):
    """Check a username safely when the store is missing or unreadable."""
    if not isinstance(username, str):
        return False
    try:
        with Path(path).open("r", encoding="utf-8") as file, _locked_users(file, shared=True):
            return username.strip().casefold() in _read_users(file)
    except (OSError, UnicodeError):
        return False


def register_user(username, password, path=USERS_FILE):
    """Validate and save a new user, returning a success flag and message."""
    if not isinstance(username, str):
        return False, "Username must be text."
    username = username.strip()
    if not username or "," in username:
        return False, "Username cannot be empty or contain a comma."
    if not username.isprintable():
        return False, "Username cannot contain newlines or control characters."
    if not isinstance(password, str):
        return False, "Password must be text."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    try:
        hashed = generate_hash(password)
    except ValueError:
        return False, "Password must be valid UTF-8 text of at most 72 bytes."

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+", encoding="utf-8", newline="") as file, _locked_users(file):
            # Keep duplicate checking and writing under the same lock.
            file.seek(0)
            contents = file.read()
            file.seek(0)
            if username.casefold() in _read_users(file):
                return False, "That username is already taken."
            file.seek(0, 2)
            original_end = file.tell()
            separator = "\n" if contents and not contents.endswith("\n") else ""
            try:
                file.write(f"{separator}{username},{hashed}\n")
                file.flush()
            except OSError:
                # Remove a partial row so a failed save can be retried.
                file.seek(original_end)
                file.truncate()
                raise
    except (OSError, UnicodeError):
        return False, "Could not save the user file. Please try again."
    return True, "Registered. You can log in now."


def login_user(username, password, path=USERS_FILE):
    """Check credentials and use the same failure message for unknown users."""
    if not isinstance(username, str) or not isinstance(password, str):
        return False, LOGIN_FAILED
    try:
        with Path(path).open("r", encoding="utf-8") as file, _locked_users(file, shared=True):
            stored_hash = _read_users(file).get(username.strip().casefold())
    except (OSError, UnicodeError):
        return False, LOGIN_FAILED
    if stored_hash is not None and is_valid_hash(password, stored_hash):
        return True, "Welcome back!"
    return False, LOGIN_FAILED


def main():
    """Offer registration, login and exit without displaying passwords."""
    while True:
        print("\n1. Register\n2. Log in\n3. Exit")
        try:
            choice = input("> ").strip()
            if choice == "3":
                print("Goodbye!")
                return
            if choice not in ("1", "2"):
                print("Choose 1, 2 or 3.")
                continue
            name = input("Username: ")
            password = getpass("Password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if choice == "1":
            ok, message = register_user(name, password)
        else:
            ok, message = login_user(name, password)
        print(("OK: " if ok else "NO: ") + message)


if __name__ == "__main__":
    main()
