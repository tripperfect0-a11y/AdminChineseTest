import os
import requests
import uuid
from flask import Flask, request, render_template, redirect, url_for, jsonify, session

# --- Supabase API Details ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 
SUPABASE_STORAGE_BUCKET = "student-images" 

# --- Flask Application Setup ---
app = Flask(__name__)
# The FLASK_SECRET_KEY is read from environment variables
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# --- Authentication Helpers ---
def is_authenticated():
    """Checks if a valid access token exists in the session."""
    return 'access_token' in session

# --- Core Routes ---

# 1. Login/Auth Route (UNIFIED FIX)
@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'GET':
        # Show the login form
        return render_template('login.html')

    if request.method == 'POST':
        # Process the login
        email = request.form.get('email')
        password = request.form.get('password')

        auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {"email": email, "password": password}

        try:
            response = requests.post(auth_url, headers=headers, json=payload)
            auth_data = response.json()
            
            if response.ok and 'access_token' in auth_data:
                session['access_token'] = auth_data['access_token']
                # FIX: Redirect to the unified add_score_route
                return redirect(url_for('add_score_route')) 
            else:
                error_message = auth_data.get('msg', 'Invalid credentials')
                return render_template('login.html', error=error_message), 401

        except requests.exceptions.RequestException:
            return render_template('login.html', error='Could not connect to authentication server.'), 500

# 2. Secure POST/GET Route (Consolidated)
@app.route('/add-score', methods=['GET', 'POST'])
def add_score_route():
    # Enforce Login: If not logged in, redirect to login page
    if not is_authenticated():
        return redirect(url_for('login_route'))
        
    if request.method == 'GET':
        return render_template('add_score.html')
        
    if request.method == 'POST':
        # 1. Generate new ID and handle file upload
        file = request.files.get('profile_photo')
        new_sid = str(uuid.uuid4()) 
        profile_photo_url = request.form.get('profile_photo') 

        if file and file.filename:
            # File Upload Logic (Complex)
            filename = f"{new_sid}-{file.filename}"
            profile_photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{filename}"
            
            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": file.content_type,
                "x-upsert": "true"
            }
            
            try:
                requests.post(
                    f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{filename}", 
                    data=file.read(), 
                    headers=headers
                ).raise_for_status()
                
            except requests.exceptions.RequestException as e:
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
            requests.post(api_url, json=data, headers=headers).raise_for_status()
            
            # Final successful redirect
            return redirect(url_for('query_score', sid=new_sid))
        except requests.exceptions.RequestException as e:
            return f"Error inserting data: {e}", 500

# 3. Read Route (Public)
@app.route('/queryScore.do')
def query_score():
    # ... your existing logic for the query_score route remains the same (not repeated for brevity) ...
    pass # Assume this block is in app.py

if __name__ == '__main__':
    app.run(debug=True)