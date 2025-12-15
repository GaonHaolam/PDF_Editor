from functools import wraps
from flask import redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
import os
import shutil
import glob
from werkzeug.utils import secure_filename

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
    for folder in folders_to_clean:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error removing {f}: {e}")


def get_user_folder(user_id):
    """Get the base folder for a specific user."""
    return os.path.join('edited_files', str(user_id))


def get_user_temp_dir(user_id, type='old'):
    """
    Get the temp directory for a user.
    type: 'old' (uploads) or 'new' (processed)
    """
    base = get_user_folder(user_id)
    return os.path.join(base, 'temp', type)


def init_user_folders(user_id):
    """Ensure user folders exist."""
    old_dir = get_user_temp_dir(user_id, 'old')
    new_dir = get_user_temp_dir(user_id, 'new')
    saved_dir = os.path.join(get_user_folder(user_id), 'saved')
    
    os.makedirs(old_dir, exist_ok=True)
    os.makedirs(new_dir, exist_ok=True)
    os.makedirs(saved_dir, exist_ok=True)
    
    return {
        'old': old_dir,
        'new': new_dir,
        'saved': saved_dir
    }


def save_user_file(user_id, filename, folder_type):
    """Save a file to the user's permanent library."""
    if folder_type == 'processed':
        src_dir = get_user_temp_dir(user_id, 'new')
    elif folder_type == 'old':
        src_dir = get_user_temp_dir(user_id, 'old')
    else:
        return False, "Invalid folder type"

    src_path = os.path.join(src_dir, filename)
    if not os.path.exists(src_path):
        return False, "File not found"

    saved_dir = os.path.join(get_user_folder(user_id), 'saved')
    dst_path = os.path.join(saved_dir, filename)

    try:
        shutil.copy2(src_path, dst_path)
        return True, "File saved successfully"
    except Exception as e:
        return False, str(e)


def save_uploaded_file(file, user_id):
    """
    Securely save an uploaded file to the user's temp/old directory.
    If file exists, appends (1), (2), etc.
    Returns (filename, filepath)
    """
    original_filename = secure_filename(file.filename)
    old_dir = get_user_temp_dir(user_id, 'old')
    
    # Split filename and extension
    base, ext = os.path.splitext(original_filename)
    
    filename = original_filename
    counter = 1
    
    # While file exists, add counter
    while os.path.exists(os.path.join(old_dir, filename)):
        filename = f"{base}({counter}){ext}"
        counter += 1
        
    filepath = os.path.join(old_dir, filename)
    file.save(filepath)
    return filename, filepath


def get_file_url(user_id, folder_type, filename):
    """Generate the URL for a served file."""
    if folder_type not in ['old', 'new', 'saved']:
        return None
    # Adjust path segment based on folder type for the URL structure if needed
    # Currently app serves from /edited_files/<user_id>/...
    # folder_type mapping: 'old' -> 'temp/old', 'new' -> 'temp/new', 'saved' -> 'saved'
    
    subpath = ""
    if folder_type == 'saved':
        subpath = 'saved'
    else:
        subpath = f"temp/{folder_type}"
        
    return f"/edited_files/{user_id}/{subpath}/{filename}"

