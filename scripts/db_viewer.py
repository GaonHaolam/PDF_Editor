import os
import shutil
from cs50 import SQL
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Ensure we access the DB and files in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'pdfeditor.db')
EDITED_FILES_DIR = os.path.join(BASE_DIR, 'edited_files')

db = SQL(f"sqlite:///{DB_PATH}")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    users = db.execute("SELECT * FROM users")
    html = """
    <html>
        <head>
            <title>DB Viewer</title>
            <style>
                body { font-family: sans-serif; padding: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .btn-delete { 
                    background-color: #ff4d4d; color: white; border: none; 
                    padding: 5px 10px; cursor: pointer; border-radius: 4px;
                }
                .btn-delete:hover { background-color: #cc0000; }
            </style>
        </head>
        <body>
            <h1>Users Table</h1>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Hash</th>
                    <th>Actions</th>
                </tr>
                {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.hash[:20] }}...</td>
                        <td>
                            <form action="{{ url_for('delete', user_id=user.id) }}" method="POST" onsubmit="return confirm('Are you sure? This will delete the user and all their files.');" style="margin:0;">
                                <button type="submit" class="btn-delete">Delete</button>
                            </form>
                        </td>
                    </tr>
                {% else %}
                    <tr><td colspan="4">No users found</td></tr>
                {% endfor %}
            </table>
        </body>
    </html>
    """
    return render_template_string(html, users=users)

@app.route("/delete/<int:user_id>", methods=["POST"])
def delete(user_id):
    # 1. Delete user files
    user_folder = os.path.join(EDITED_FILES_DIR, str(user_id))
    try:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
            print(f"Deleted files for user {user_id}")
    except Exception as e:
        print(f"Error deleting user files: {e}")

    # 2. Delete user from DB
    try:
        db.execute("DELETE FROM users WHERE id = ?", user_id)
    except Exception as e:
        print(f"Error deleting user from DB: {e}")
        
    return redirect("/")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
