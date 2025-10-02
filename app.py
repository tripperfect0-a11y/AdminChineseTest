import os
import requests
import uuid
from flask import Flask, request, render_template, redirect, url_for, jsonify, session

# --- Supabase API Details ---
# IMPORTANT: These are read from Vercel environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_STORAGE_BUCKET = "Student Images" # Ensure this matches your exact bucket name (Case-sensitive)

# --- Flask Application Setup ---
app = Flask(__name__)
# Secret key is read from FLASK_SECRET_KEY environment variable
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# --- Authentication Helpers ---
def is_authenticated():
    """Checks if a valid access token exists in the session."""
    return 'access_token' in session

# --- 1. Login/Auth Route (UNIFIED) ---
@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        
        headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
        payload = {"email": email, "password": password}

        try:
            response = requests.post(auth_url, headers=headers, json=payload)
            auth_data = response.json()
            
            if response.ok and 'access_token' in auth_data:
                session['access_token'] = auth_data['access_token']
                # FIX: Redirect to the add_score_route
                return redirect(url_for('add_score_route')) 
            else:
                error_message = auth_data.get('msg', 'Invalid credentials')
                return render_template('login.html', error=error_message), 401

        except requests.exceptions.RequestException:
            return render_template('login.html', error='Could not connect to authentication server.'), 500

# --- 2. Secure POST/GET Route (UNIFIED & WITH FILE UPLOAD) ---
@app.route('/add-score', methods=['GET', 'POST'])
def add_score_route():
    # Enforce Login
    if not is_authenticated():
        return redirect(url_for('login_route'))
        
    if request.method == 'GET':
        return render_template('add_score.html')
        
    if request.method == 'POST':
        # 1. File Upload Logic
        file = request.files.get('profile_photo')
        new_sid = str(uuid.uuid4()) 
        profile_photo_url = request.form.get('profile_photo')

        if file and file.filename:
            filename = f"{new_sid}-{file.filename}"
            profile_photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{filename}"
            
            # Security Headers for Storage API
            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": file.content_type,
                "x-upsert": "true"
            }
            
            try:
                # POST request to Supabase Storage
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
            "profile_photo": profile_photo_url
        }
        
        data = {k: v for k, v in data.items() if v} # Clean empty values
        
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
            
            return redirect(url_for('query_score', sid=new_sid))
        except requests.exceptions.RequestException as e:
            return f"Error inserting data: {e}", 500
        except Exception as e:
            return f"An internal server error occurred: {e}", 500

# 3. Read Route (Public)
@app.route('/queryScore.do')
def query_score():
    """Handles the query and fetches data from Supabase."""
    student_id = request.args.get('sid')
    if not student_id:
        return "Student ID is missing.", 400

    api_url = f"{SUPABASE_URL}/rest/v1/scores"

    # Headers use the public key for read access
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {"sid": f"eq.{student_id}", "select": "*"}

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()

        if data and len(data) > 0:
            student_data = data[0]
            return render_template('results.html', student=student_data)
        else:
            return "Student ID not found.", 404
    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}", 500
    except Exception as e:
        return f"An internal server error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)