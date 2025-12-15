import os

from werkzeug.utils import secure_filename
from slice_and_reorder.slice import slice_pdf
from slice_and_reorder.reorder import reorder_pdf
from slice_and_reorder.utils import delete_page_from_pdf

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from helpers import login_required, register_user, authenticate_user, validate_login, validate_register, clean_folders

# Configure application
app = Flask(__name__)

# Configure upload and output folders
UPLOAD_FOLDER = 'static/uploads' # For OCR etc
# Slice & Reorder specific folders
OLD_FOLDER = 'static/slice_and_reorder/old'
NEW_FOLDER = 'static/slice_and_reorder/new'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OLD_FOLDER, exist_ok=True)
os.makedirs(NEW_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OLD_FOLDER'] = OLD_FOLDER
app.config['NEW_FOLDER'] = NEW_FOLDER

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
    # Clean folders on new login flow start (optional but good for safety)
    # Actually user said "if user session is reset empty the old and new folders".
    # session.clear() implies reset.
    clean_folders([OLD_FOLDER, NEW_FOLDER])

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

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    clean_folders([OLD_FOLDER, NEW_FOLDER])
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    clean_folders([OLD_FOLDER, NEW_FOLDER])

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
            filename = secure_filename(file.filename)
            # Save to OLD_FOLDER
            input_path = os.path.join(app.config['OLD_FOLDER'], filename)
            file.save(input_path)

            # Intermediate path (result of slicing)
            # We can save this in OLD_FOLDER too as a temp file
            sliced_filename = f"sliced_temp_{filename}"
            sliced_path = os.path.join(app.config['OLD_FOLDER'], sliced_filename)

            # Final Output path (in NEW_FOLDER)
            final_filename = f"processed_{filename}"
            final_path = os.path.join(app.config['NEW_FOLDER'], final_filename)

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
                # 1. Slice
                # Pass action to slice_pdf if it needs it for LTR/RTL ordering decisions 
                # OR we rely on reorder.py to do ALL ordering? 
                # User said: "slice.py from there to reorder.py taking the button that was picked"
                # But slice.py ALSO takes 'mode' currently to decide usage. 
                # slice.py logic I wrote:
                # if "rtl" in mode -> output Right Page then Left Page
                # else -> output Left Page then Right Page.
                # If reorder.py expects logical pages in order, slice.py should probably just output VISUAL LEFT then VISUAL RIGHT?
                # Actually, my previous slice.py implementation alreayd handles RTL/LTR sort.
                # If I use slice.py's sorting, maybe reorder.py's double-sorting will mess it up?
                # User: "slice.py from there to reorder.py taking the button that was picked"
                # Let's assume slice.py purely cuts (maybe we should pass a 'raw' mode to it? or just let it do its best).
                # The reorder.py I read seems to expect inputs in a specific order (sequence of spreads).
                # My slice.py sorts:
                # RTL Mode: Page 1 (Right), Page 2 (Left).
                # LTR Mode: Page 1 (Left), Page 2 (Right).
                # This seems "Correct" for a viewing persepctive.
                # reorder.py logic:
                # It takes the pages linearily 0..N.
                # If slice.py produced [P1, P2] for Spread 1.
                # Then reorder.py maps them.
                # If slice.py produced "Correct Order" linear pages, then reorder.py might not need to do anything for "Spreads"?
                # Wait. "Spreads RTL" in Reorder.py: "new_order[i] = reader.pages[i+1]; new_order[i+1] = reader.pages[i]".
                # This means it SWAPS every pair.
                # If slice.py ALREADY swapped them because of "rtl" mode... then swapping again restores original order?
                # Let's check slice.py again.
                # RTL Mode in slice.py: `writer.add_page(p_right); writer.add_page(p_left)` 
                # So Output[0] = Right Half. Output[1] = Left Half.
                # Visual Right is usually Page 1 in Hebrew.
                # So Output is [Page 1, Page 2]. Correct sequence!
                # If we pass [Page 1, Page 2] to reorder.py's "Spreads RTL"...
                # Reorder Spreads RTL: swaps 0 and 1.
                # Limit: Page 2, Page 1.
                # That creates a PDF where P2 is first? That's wrong for a linear PDF reader.
                # Linear PDF should be [P1, P2, P3...].
                
                # HYPOTHESIS: `slice.py` should probably just slice VISUAL LEFT then VISUAL RIGHT (standard reading order of the spread image),
                # and let `reorder.py` handle the logical remapping.
                # OTHERWISE, we are double-correcting.
                
                # Let's force slice.py to use "ltr" (standard scan order: Left half is first part of image, Right half is second)
                # regardless of the user's choice, so that reorder.py receives consistent "Left Slice, Right Slice" stream.
                # Then reorder.py's logic (which assumes "Left=Input[0], Right=Input[1]") will work as intended.
                
                # Step 1: Slice as LTR (Left=0, Right=1)
                slice_pdf(input_path, sliced_path, mode="spreads_ltr") 
                
                # Step 2: Reorder using the User's selection
                reorder_pdf(sliced_path, final_path, mode=reorder_mode)

                # Send relative path for serving
                # Since NEW_FOLDER is 'slice_and_reorder/new', and flask needs to serve it.
                # Wait, 'slice_and_reorder' is NOT in 'static'. 
                # If I put it in root, Flask won't serve it by default unless I add a route to serve files.
                # User config: `app.config['NEW_FOLDER'] = NEW_FOLDER`.
                # I should probably use `send_from_directory` or move folders to `static/slice_and_reorder`.
                # User instruction: "put them into a folder called slice_and_reorder... integrate... when a pdf is uploded ... gets stored within a folder in the previouse folder thats called old ..."
                # If I want to serve the file in `sliced.html` via `<embed src="...">`, it MUST be accessible via HTTP.
                # So it SHOULD be in `static`.
                # Let's change OLD_FOLDER and NEW_FOLDER to be inside 'static'.
                # OLD_FOLDER = 'static/slice_and_reorder/old'
                # NEW_FOLDER = 'static/slice_and_reorder/new'
                # Pass relative path for download
                # Remove static/ prefix if needed, but usually Flask serves static files from root if configured?
                # Actually, if template uses `url_for('static', filename=...)` it's best.
                # But here we are constructing path manually. 
                # Flask default static route is /static/<path>
                
                # We need pdf_url to be web accessible.
                # app.config['NEW_FOLDER'] is 'static/slice_and_reorder/new'
                # So url is '/static/slice_and_reorder/new/processed_filename'
                
                pdf_url = f"/{app.config['NEW_FOLDER']}/{final_filename}"

                # Clean up intermediate
                if os.path.exists(sliced_path):
                    os.remove(sliced_path)

                return render_template('sliced.html', 
                                       output_file=pdf_url, # Keeping for backward compat if needed, but partial uses pdf_url
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
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Pass the relative path for the frontend (remove 'static/' prefix if served by Flask static)
            # Typically Flask serves static folder at /static/
            pdf_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"
            
            return render_template('ocr.html', pdf_url=pdf_url, filename=filename, folder_type='uploads')
    
    return render_template('ocr.html')


@app.route('/delete_page', methods=["POST"])
@login_required
def delete_page():
    import fitz
    from flask import jsonify
    
    data = request.get_json()
    filename = data.get('filename')
    page_number = data.get('page_number') # 1-based index
    folder_type = data.get('folder_type', 'uploads') # Default to uploads for backward compat
    
    if not filename or page_number is None:
         return jsonify({'success': False, 'error': 'Missing filename or page number'}), 400

    # Determine folder based on type
    if folder_type == 'processed':
        target_folder = app.config['NEW_FOLDER']
    else:
        target_folder = app.config['UPLOAD_FOLDER']

    file_path = os.path.join(target_folder, secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    try:
        success = delete_page_from_pdf(file_path, page_number)
        if success:
             return jsonify({'success': True})
        else:
             return jsonify({'success': False, 'error': 'Invalid page number'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history')
@login_required
def history():
    return render_template('history.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
