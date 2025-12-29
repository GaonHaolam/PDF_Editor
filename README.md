# PDF Slicer & Reorderer
#### Video Demo: https://youtu.be/vdTGOOvpMi8
#### Description:

The **PDF Slicer & Reorderer** is a web-based application designed to help users manipulate PDF layouts, specifically for converting digital spreads into single-page sequences. This project's idea was born when I was scanning in a large amount of booklets a couple of years ago and needed a solution to order them properly. I decided then that once I learned programming, I would solve this problem.

### Overview

The application allows users to upload a PDF, split every physical page into two logical pages (visual left and visual right), and then reorder those pages based on specific use cases: Booklet (LTR/RTL) or Spreads (LTR/RTL). It also features a personal library where users can save their processed files for future access.

### File Descriptions

* **app.py**: The main Flask application. It handles routing, session management, and the high-level logic for uploading, processing, and serving files.
* **helpers.py**: Contains utility functions for user authentication, input validation, and managing the complex directory structure required to keep user files isolated and secure.
* **slice_and_reorder/slice.py**: This module uses the `pypdf` library to perform the heavy lifting of splitting PDF pages. It calculates crop boxes based on the page's rotation (0, 90, 180, or 270 degrees) to ensure the visual "left" and "right" are correctly identified.
* **slice_and_reorder/reorder.py**: Logic for re-sequencing the sliced pages. It supports four modes: Booklet RTL, Booklet LTR, Spreads RTL, and Spreads LTR.
* **schema.sql**: Defines the SQLite database structure, which currently maintains a `users` table with hashed passwords for security.
* **scripts/db_viewer.py**: Admin utility script used to view database contents and delete users.
* **requirements.txt**: Lists the necessary Python dependencies, including `Flask`, `pypdf`, and `cs50`.
* **static/ & templates/**: These directories contain the frontend assets (CSS/JS) and HTML templates (using Jinja2) that provide the user interface for the application.

### Design Choices

#### 1. Coordinate-Based Slicing
I chose to use `pypdf`'s `cropbox` and `mediabox` properties rather than rendering the PDF to images. This ensures that the output PDF remains "vector-based," meaning text remains selectable and the file size stays relatively small compared to an image-based approach.

#### 2. Handling Rotation
A major challenge was PDFs with mixed rotations. I implemented logic in `slice.py` to check the `rotation` attribute of each page. Depending on whether a page is landscape or portrait (or upside down), the "Left" slice might actually be the bottom or top of the physical page. Handling all four 90-degree increments was essential for a robust tool.

#### 3. Temporary vs. Permanent Storage
To prevent the server from being bogged down by abandoned files, I implemented a two-tier storage system. Files are initially processed in a `temp` directory. Users must explicitly "Save" a file to move it to their `saved` library. I also included a `cleanup_temp` route to purge temporary files when a user logs out.

#### 4. Reordering Logic
The reordering math (calculating `out_low` and `out_high` indices) was designed to handle the complexity of "Booklet" printing, where the first and last pages must be on the same physical sheet. By separating the "slice" and "reorder" steps, the code remains modular and easier to debug.

### How to Run
1. Install dependencies: `pip install -r requirements.txt`.
2. Initialize the database: `sqlite3 pdfeditor.db < schema.sql`.
3. Run the Flask app: `python app.py`.
4. Register an account and upload your first PDF!