DANBOORU LOCAL GALLERY UPGRADE
==============================

This version keeps your existing danbooru.duckdb database.
You DO NOT need to rerun download.py or build.py.

1. Stop the Flask server with Ctrl+C.

2. Copy these files into D:\Development\danbooru-local\ and allow them to replace
   the previous app.py, templates\index.html, and static\style.css.

   New file:
     static\gallery.js

3. Your folder should look like:

   danbooru-local\
     app.py
     danbooru.duckdb
     templates\
       index.html
     static\
       style.css
       gallery.js

4. Start it again:

   .\.venv\Scripts\Activate.ps1
   python app.py

5. Open:

   http://127.0.0.1:5000

How previews work
-----------------
The browser searches your local DuckDB, exactly as before. For visible cards only,
gallery.js requests the official JSON endpoint for that individual post and uses the
preview_file_url returned by Danbooru. Requests are limited to 4 at a time and preview
URLs are cached in your browser for 7 days.

If Danbooru doesn't return a preview URL for a post, the card says "Preview unavailable".
The app does not derive media URLs from hashes.
