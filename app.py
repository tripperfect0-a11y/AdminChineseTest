import os
import requests
from flask import Flask, request, render_template

# --- Supabase API Details ---
# Store these securely as environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
# --- Flask Application Setup ---
app = Flask(__name__)

# Route to serve the form page
@app.route('/add-score', methods=['GET'])
def add_score_form():
    return render_template('add_score.html')

# Route to handle the form submission and add data
@app.route('/add-score', methods=['POST'])
def add_score():
    data = {
        "sid": request.form.get('sid'),
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
        "profile_photo": request.form.get('profile_photo')
    }

    # Remove fields with empty values to avoid API errors
    data = {k: v for k, v in data.items() if v}

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    api_url = f"{SUPABASE_URL}/rest/v1/scores"

    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        
        # Redirect to the results page with the new ID
        return redirect(url_for('query_score', sid=request.form.get('sid')))
    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}", 500
    except Exception as e:
        return f"An internal server error occurred: {e}", 500

@app.route('/queryScore.do')
def query_score():
    """Handles the query and fetches data from Supabase."""
    student_id = request.args.get('sid')
    if not student_id:
        return "Student ID is missing.", 400

    # The API URL to query your 'scores' table
    api_url = f"{SUPABASE_URL}/rest/v1/scores"

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
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()

        if data and len(data) > 0:
            student_data = data[0]
            # Render the original HTML template with the fetched data
            return render_template('results.html', student=student_data)
        else:
            return "Student ID not found.", 404
    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}", 500
    except Exception as e:
        return f"An internal server error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)