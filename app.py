import os
import requests
import uuid
from flask import Flask, request, render_template, redirect, url_for, jsonify, session

# --- Supabase API Details ---
# Reads keys from Vercel environment variables (os.environ.get)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Used for secure POST

# --- Flask Application Setup ---
app = Flask(__name__)
# IMPORTANT: REPLACE THIS WITH A LONG, RANDOM STRING IN PRODUCTION
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# --- Authentication Helpers ---
def is_authenticated():
    """Checks if a valid access token exists in the session."""
    return 'access_token' in session

# --- Core Routes ---

# 1. Login Routes (The Security Layer)
@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(auth_url, headers=headers, json=payload)
        auth_data = response.json()
        
        if response.ok and 'access_token' in auth_data:
            session['access_token'] = auth_data['access_token']
            return redirect(url_for('add_score_form'))
        else:
            error_message = auth_data.get('msg', 'Invalid credentials')
            return render_template('login.html', error=error_message), 401

    except requests.exceptions.RequestException:
        return render_template('login.html', error='Could not connect to authentication server.'), 500

# 2. Secure POST Route
@app.route('/add-score', methods=['GET', 'POST'])
def add_score():
    # Enforce Login: If not logged in, redirect to login page
    if not is_authenticated():
        return redirect(url_for('login_form'))
        
    if request.method == 'GET':
        # Show the form
        return render_template('add_score.html')
        
    if request.method == 'POST':
        # FIX 1: Generate new ID on every POST request (Moved inside the function)
        new_sid = str(uuid.uuid4()) 
        
        data = {
            # FIX: Use the newly generated ID for the POST request
            "sid": new_sid, 
            "name_on_certificate": request.form.get('name_on_certificate'),
            "chinese_name": request.form.get('chinese_name'),
            "nationality": request.form.get('nationality'),
            "gender": request.form.get('gender'),
            # ... all other fields from the form ...
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
            # FIX 2: We need to handle the file upload here. 
            # For now, we will set it to None, as the full file upload logic is complex.
            "profile_photo": None 
        }

        # Use the Service Key for admin-level POST (as we planned)
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
            return f"An API error occurred: {e}", 500
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

    # Use the public key for read access
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {
        "sid": f"eq.{student_id}",
        "select": "*"
    }

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