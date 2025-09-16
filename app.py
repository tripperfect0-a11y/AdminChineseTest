import os
import requests
from flask import Flask, request, render_template

# --- Supabase API Details ---
# Store these securely as environment variables
SUPABASE_URL = "https://oltrxsrigdwgjhqdzgag.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9sdHJ4c3JpZ2R3Z2pocWR6Z2FnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5OTczNzgsImV4cCI6MjA3MzU3MzM3OH0.OIL7d4lyNB1A5BF3fHIgq1tsux5wxiIAls2IiVKeG8k"

# --- Flask Application Setup ---
app = Flask(__name__)

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