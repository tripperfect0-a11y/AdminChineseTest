import os
import requests
import uuid
from flask import Flask, request, render_template, redirect, url_for, jsonify, session

# --- Supabase API Details ---
# Reads keys from Vercel environment variables (os.environ.get)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Service Key is for POST/Storage Upload
SUPABASE_STORAGE_BUCKET = "student-images" # Your Supabase Storage Bucket Name (Adjust if needed)

# --- Flask Application Setup ---
app = Flask(__name__)
# The FLASK_SECRET_KEY is read from environment variables
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# --- Authentication Helpers ---
def is_authenticated():
    """Checks if a valid access token exists in the session."""
    return 'access_token' in session

# --- Core Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... Login logic is correct and remains the same (not repeated for brevity) ...
    pass # Assume this block is in app.py

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    # ... rest of the login logic ...
    
    # SUCCESSFUL LOGIN REDIRECT:
    # return redirect(url_for('add_score_route')) 
    # ...
    pass # Assume this block is in app.py

# 2. Secure POST/GET Route (Consolidated)
@app.route('/add-score', methods=['GET', 'POST'])
def add_score_route():
    # Enforce Login: If not logged in, redirect to login page
    if not is_authenticated():
        return redirect(url_for('login_form'))
        
    if request.method == 'GET':
        # Logic for GET request (Show the form)
        return render_template('add_score.html')
        
    if request.method == 'POST':
        # 1. Generate new ID and handle file upload
        file = request.files.get('profile_photo')
        new_sid = str(uuid.uuid4()) 
        profile_photo_url = request.form.get('profile_photo') # Default to URL if provided

        if file and file.filename:
            # Generate unique filename for storage
            filename = f"{new_sid}-{file.filename}"
            
            # Construct the public URL first (used later)
            profile_photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{filename}"
            
            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": file.content_type,
                "x-upsert": "true" 
            }
            
            try:
                # API Call to Upload the File
                response = requests.post(
                    f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{filename}", 
                    data=file.read(), 
                    headers=headers
                )
                response.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                # This returns the error if the file upload fails
                return f"Error uploading image to storage: {e}", 500

        # 2. Prepare and Insert Data
        data = {
            "sid": new_sid, 
            "name_on_certificate": request.form.get('name_on_certificate'),
            "chinese_name": request.form.get('chinese_name'),
            "nationality": request.form.get('nationality'),
            "gender": request.form.get('gender'),
            "test_location": request.form.get('test_location'),
            "ticket_no": request.form.get('ticket_no'),
            "certificate_no": request.form.get('certificate_no'),
            "test_type": request.form.get('test_type'),
            "test_time": request.form.get('test_time'),
            "total_score": request.form.get('total_score'),
            "status": request.form.get('status'),
            "listening_score": request.form.get('listening_score'),
            "reading_score": request.form.get('reading_score'),
            "writing_score": request.form.get('writing_score'),
            "oral_score": request.form.get('oral_score'),
            "oral_status": request.form.get('oral_status'),
            "profile_photo": profile_photo_url # Final URL is stored here
        }

        # Remove fields with empty values
        data = {k: v for k, v in data.items() if v}
        
        # API Call to Insert the Record
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        api_url = f"{SUPABASE_URL}/rest/v1/scores"

        try:
            response = requests.post(api_url, json=data, headers=headers)
            response.raise_for_status()
            
            # Redirect to the results page with the new ID
            return redirect(url_for('query_score', sid=new_sid))
        except requests.exceptions.RequestException as e:
            return f"Error inserting data: {e}", 500
        except Exception as e:
            return f"An internal server error occurred: {e}", 500

# 3. Read Route (Public)
@app.route('/queryScore.do')
def query_score():
    # ... your existing logic for the query_score route remains the same ...
    pass # Assume this block is in app.py

if __name__ == '__main__':
    app.run(debug=True)