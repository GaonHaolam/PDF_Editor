from functools import wraps
from flask import redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
import os
import shutil

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def register_user(db, username, password):
    """Register a new user in the database."""
    hash = generate_password_hash(password)
    try:
        user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        return user_id
    except ValueError:
        return None 


def authenticate_user(db, username, password):
    """authenticate a user."""
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        return None
    return rows[0]["id"]


def check_input_provided(field_value, field_name):
    """Check if input is provided."""
    if not field_value:
        return f"Must provide {field_name}"
    return None


def check_passwords_match(password, confirmation):
    """Check if passwords match."""
    if password != confirmation:
        return "Passwords don't match"
    return None


def validate_login(username, password):
    """Validate login input."""
    error = check_input_provided(username, "username")
    if error:
        return error
    
    error = check_input_provided(password, "password")
    if error:
        return error
    
    return None


def validate_register(username, password, confirmation):
    """Validate registration input."""
    error = check_input_provided(username, "username")
    if error:
        return error

    error = check_input_provided(password, "password")
    if error:
        return error

    error = check_input_provided(confirmation, "confirmation")
    if error:
        return error

    error = check_passwords_match(password, confirmation)
    if error:
        return error
        
    return None



def clean_folders(folders_to_clean):
    """Empty the specified folders."""
    import glob
    for folder in folders_to_clean:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error removing {f}: {e}")

