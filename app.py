import sqlite3
from flask import Flask, request, render_template

# The database will now be in-memory for each request
def get_db_connection():
    conn = sqlite3.connect(':memory:')
    return conn

def init_db(conn):
    """Creates and initializes the database with a more detailed schema."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE scores (
            sid TEXT PRIMARY KEY,
            name_on_certificate TEXT,
            chinese_name TEXT,
            nationality TEXT,
            gender TEXT,
            test_location TEXT,
            ticket_no TEXT,
            certificate_no TEXT,
            test_type TEXT,
            test_time TEXT,
            total_score TEXT,
            status TEXT,
            listening_score INTEGER,
            reading_score INTEGER,
            writing_score INTEGER,
            oral_score INTEGER
        )
    ''')
    
    # Sample data to match your HTML template
    cursor.execute('''
        INSERT INTO scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('c2tActR9Wb', 'RAJAMANI KULASEKARARAJAAMANISIVAVIGNESWARA', '', '印度', '男', 
          '深圳大学（网考）', 'H42506899970100009 H82506899970100013', 'H42506899970100013', 
          'H42507065464', 'HSK四级', '19-Jul-2025', '135', '不合格', 58, 38, 39, 21))
    
    conn.commit()

# --- Flask Application Setup ---
app = Flask(__name__)

@app.route('/queryScore.do')
def query_score():
    """Handles requests and renders the HTML template."""
    conn = get_db_connection()
    init_db(conn) # Initialize the in-memory database for this request

    student_id = request.args.get('sid')
    if not student_id:
        return "Student ID is missing.", 400

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scores WHERE sid = ?", (student_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        student_data = {
            "sid": result[0],
            "name": result[1],
            "chinese_name": result[2],
            "nationality": result[3],
            "gender": result[4],
            "test_location": result[5],
            "ticket_no": result[6],
            "certificate_no": result[7],
            "test_type": result[8],
            "test_time": result[9],
            "total_score": result[10],
            "status": result[11],
            "listening_score": result[12],
            "reading_score": result[13],
            "writing_score": result[14],
            "oral_score": result[15]
        }
        return render_template('results.html', student=student_data)
    else:
        return "Student ID not found.", 404

if __name__ == '__main__':
    conn = get_db_connection()
    init_db(conn)
    app.run(debug=True)