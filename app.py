from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'pitchforge_mvp_key'  # Change this in prod!

# Init DB
def init_db():
    conn = sqlite3.connect('pitchforge.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pitches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  idea_summary TEXT NOT NULL,
                  target_audience TEXT,
                  funding_ask REAL,
                  timeline_months INTEGER,
                  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        idea_summary = request.form['idea_summary']
        target_audience = request.form.get('target_audience', '')
        funding_ask_str = request.form.get('funding_ask', '')
        timeline_months_str = request.form.get('timeline_months', '')
        
        # Basic validation
        if not email or not idea_summary:
            flash('Email and idea summary are required!')
            return redirect(url_for('index'))
        
        # Safe number coercion (blanks = 0, errors flash)
        try:
            funding_ask = float(funding_ask_str) if funding_ask_str else 0.0
            timeline_months = int(timeline_months_str) if timeline_months_str else 0
        except ValueError:
            flash('Funding ask and timeline must be valid numbers (or leave blank for defaults)!')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('pitchforge.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pitches (email, idea_summary, target_audience, funding_ask, timeline_months)
                     VALUES (?, ?, ?, ?, ?)''',
                  (email, idea_summary, target_audience, funding_ask, timeline_months))
        conn.commit()
        conn.close()
        
        flash('Pitch submitted! Thanks for testing—check your email for a fake confirmation.')
        return redirect(url_for('success'))
    
    return render_template('form.html')

@app.route('/success')
def success():
    return '''
    <html>
        <head><title>PitchForge MVP</title></head>
        <body>
            <h1>Success! Your pitch is forged.</h1>
            <p>We'll review it soon. <a href="/">Submit another?</a></p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
