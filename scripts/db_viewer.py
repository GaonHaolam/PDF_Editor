

from cs50 import SQL
from flask import Flask, render_template_string

app = Flask(__name__)
db = SQL("sqlite:///pdfeditor.db")

@app.route("/")
def index():
    users = db.execute("SELECT * FROM users")
    html = """
    <html>
        <head><title>DB Viewer</title></head>
        <body>
            <h1>Users Table</h1>
            <table border="1">
                <tr><th>ID</th><th>Username</th><th>Hash</th></tr>
                {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.hash }}</td>
                    </tr>
                {% endfor %}
            </table>
        </body>
    </html>
    """
    return render_template_string(html, users=users)

if __name__ == "__main__":
    app.run(port=5001)
