from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this for production!
DATABASE = 'mood_journal.db'

# --- REPLACE THIS WITH YOUR API KEY ---
# Get it from: https://huggingface.co/settings/tokens
HF_API_KEY = "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"  # <-- PUT YOUR KEY INSIDE THESE QUOTES
# --------------------------------------
HF_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"

# Database setup for Windows
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Hugging Face API call to analyze emotion
def query_hf_api(payload):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

def analyze_emotion(text):
    """
    Sends text to Hugging Face API and returns the dominant emotion and its score.
    """
    if not HF_API_KEY or HF_API_KEY == "YOUR_HUGGING_FACE_API_KEY_HERE":
        return "Error: Add your API Key to app.py", 0.0

    try:
        output = query_hf_api({"inputs": text})
        
        if isinstance(output, list):
            # Find the emotion with the highest score
            dominant_emotion = max(output[0], key=lambda x: x['score'])
            return dominant_emotion['label'], round(dominant_emotion['score'], 2)
        elif isinstance(output, dict) and 'error' in output:
            return f"Model Loading: {output['error']}", 0.0
        else:
            return "Unexpected API Response", 0.0

    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return "API Error", 0.0

# App Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        journal_content = request.form['content']
        emotion, score = analyze_emotion(journal_content)

        db = get_db()
        db.execute(
            'INSERT INTO journal_entries (content, emotion_label, emotion_score) VALUES (?, ?, ?)',
            (journal_content, emotion, score)
        )
        db.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_entry.html')

@app.route('/dashboard')
def dashboard():
    db = get_db()
    entries = db.execute('SELECT * FROM journal_entries ORDER BY created_at DESC').fetchall()
    
    chart_data = db.execute('''
        SELECT emotion_label, emotion_score, created_at
        FROM journal_entries
        ORDER BY created_at DESC
        LIMIT 7
    ''').fetchall()
    chart_data = list(reversed(chart_data))

    return render_template('dashboard.html', entries=entries, chart_data=chart_data)

# Initialize the app
if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("Database initialized!")
    print("Starting server... Go to: http://127.0.0.1:5000")
    app.run(debug=True)