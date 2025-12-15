import os
from datetime import datetime

from slice_and_reorder.slice import slice_pdf
from slice_and_reorder.reorder import reorder_pdf
from slice_and_reorder.utils import delete_page_from_pdf

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, jsonify
from flask_session import Session

from helpers import login_required, register_user, authenticate_user, validate_login, validate_register, clean_folders, init_user_folders, get_user_temp_dir, get_user_folder, save_user_file, save_uploaded_file, get_file_url

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "super_secret_key"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pdfeditor.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def home():
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        error = validate_login(username, password)
        if error:
            flash(error, "error")
            return render_template("login.html")

        # Authenticate user
        user_id = authenticate_user(db, username, password)
        
        if user_id is None:
            flash("Invalid username and/or password", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = user_id
        
        # Initialize user folders
        init_user_folders(user_id)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        old = get_user_temp_dir(user_id, 'old')
        new = get_user_temp_dir(user_id, 'new')
        clean_folders([old, new])
        
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        error = validate_register(username, password, confirmation)
        if error:
            flash(error, "error")
            return render_template("register.html")

        user_id = register_user(db, username, password)
        
        if user_id is None:
             flash("User name is already in use", "error")
             return render_template("register.html")

        session["user_id"] = user_id
        init_user_folders(user_id)
        return redirect("/")


@app.route('/slice', methods=["GET", "POST"])
@login_required
def slice():
    if request.method == "POST":
        # Check if file is present
        if 'pdf_file' not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
        
        file = request.files['pdf_file']
        action = request.form.get('action')

        if file.filename == '':
            flash("No selected file", "error")
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            user_id = session["user_id"]
            
            # Save uploaded file using helper
            filename, input_path = save_uploaded_file(file, user_id)
            
            # Define other paths
            old_dir = get_user_temp_dir(user_id, 'old')
            new_dir = get_user_temp_dir(user_id, 'new')

            sliced_filename = f"sliced_temp_{filename}"
            sliced_path = os.path.join(old_dir, sliced_filename)

            final_filename = f"processed_{filename}"
            final_path = os.path.join(new_dir, final_filename)

            # Map action string to reorder mode
            mode_map = {
                'booklet_rtl': 1,
                'booklet_ltr': 2,
                'spreads_rtl': 3,
                'spreads_ltr': 4
            }
            
            reorder_mode = mode_map.get(action)
            if not reorder_mode:
                flash("Invalid action selected", "error")
                return redirect(request.url)

            # Process file
            try:
                # Step 1: Slice as LTR (Left=0, Right=1)
                slice_pdf(input_path, sliced_path) 
                
                # Step 2: Reorder using the User's selection
                reorder_pdf(sliced_path, final_path, mode=reorder_mode)
                
                # Generate URL using helper
                pdf_url = get_file_url(user_id, 'new', final_filename)

                # Clean up intermediate
                if os.path.exists(sliced_path):
                    os.remove(sliced_path)

                return render_template('sliced.html', 
                                       output_file=pdf_url, 
                                       pdf_url=pdf_url,
                                       filename=final_filename,
                                       folder_type='processed')
                                       
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(request.url)

        flash("Invalid file type", "error")
        return redirect(request.url)

    return render_template('slice.html')


@app.route('/ocr', methods=["GET", "POST"])
@login_required
def ocr():
    if request.method == "POST":
        if 'pdf_file' not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
        
        file = request.files['pdf_file']
        # Language would be used here later
        # language = request.form.get('language')

        if file.filename == '':
            flash("No selected file", "error")
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            user_id = session["user_id"]
            
            # Save using helper
            filename, _ = save_uploaded_file(file, user_id)
        
            # Generate URL using helper
            pdf_url = get_file_url(user_id, 'old', filename)
            
            return render_template('ocr.html', pdf_url=pdf_url, filename=filename, folder_type='old')
    
    return render_template('ocr.html')


@app.route('/history')
@login_required
def history():
    user_id = session.get("user_id")
    saved_dir = os.path.join(get_user_folder(user_id), 'saved')
    
    files_data = []
    if os.path.exists(saved_dir):
        for f in os.listdir(saved_dir):
            path = os.path.join(saved_dir, f)
            if os.path.isfile(path):
                stats = os.stat(path)
                files_data.append({
                    'name': f,
                    'size': f"{stats.st_size / 1024:.1f} KB",
                    'date': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'url': get_file_url(user_id, 'saved', f)
                })
                
    return render_template('history.html', files=files_data)


@app.route('/edited_files/<path:filename>')
@login_required
def serve_file(filename):
    # Security: Ensure user can only access their own folder
    user_id = session.get("user_id")
    expected_prefix = f"{user_id}/"
    if not filename.startswith(expected_prefix):
         return "Unauthorized", 403
         
    return send_from_directory('edited_files', filename)


@app.route('/delete_page', methods=['POST'])
@login_required
def delete_page():
    data = request.get_json()
    filename = data.get('filename')
    page_number = data.get('page_number')
    folder_type = data.get('folder_type')

    if not filename or not page_number or not folder_type:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    user_id = session["user_id"]
    if folder_type == 'processed':
        folder = get_user_temp_dir(user_id, 'new')
    elif folder_type == 'old':
        folder = get_user_temp_dir(user_id, 'old')
    else:
         return jsonify({'success': False, 'error': 'Invalid folder type'}), 400

    file_path = os.path.join(folder, filename)

    try:
        success = delete_page_from_pdf(file_path, int(page_number))
        if success:
             return jsonify({'success': True})
        else:
             return jsonify({'success': False, 'error': 'Failed to delete page'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
         return jsonify({'success': False, 'error': 'Missing filename'}), 400
         
    user_id = session["user_id"]
    saved_dir = os.path.join(get_user_folder(user_id), 'saved')
    file_path = os.path.join(saved_dir, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cleanup_temp', methods=['POST'])
@login_required
def cleanup_temp():
    user_id = session.get("user_id")
    if user_id:
        old = get_user_temp_dir(user_id, 'old')
        new = get_user_temp_dir(user_id, 'new')
        clean_folders([old, new])
    return '', 204


@app.route('/save_file', methods=['POST'])
@login_required
def save_file():
    data = request.get_json()
    filename = data.get('filename')
    folder_type = data.get('folder_type')

    if not filename or not folder_type:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    user_id = session["user_id"]
    success, message = save_user_file(user_id, filename, folder_type)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
