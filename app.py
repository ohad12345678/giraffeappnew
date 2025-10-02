from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

USERS = {
    "headquarters": {"password": "admin123", "role": "headquarters", "name": "מטה ראשי"},
    "restaurant1": {"password": "rest123", "role": "restaurant", "name": "מסעדה 1"},
    "restaurant2": {"password": "rest123", "role": "restaurant", "name": "מסעדה 2"}
}

QUALITY_QUESTIONS = [
    {"id": "temp", "question": "טמפרטורת המזון תקינה?", "type": "yesno"},
    {"id": "freshness", "question": "טריות המוצרים", "type": "rating"},
    {"id": "cleanliness", "question": "ניקיון המטבח", "type": "rating"},
    {"id": "storage", "question": "אחסון תקין", "type": "yesno"},
    {"id": "expiry", "question": "תאריכי תפוגה בתוקף", "type": "yesno"},
    {"id": "notes", "question": "הערות נוספות", "type": "text"}
]

submissions = []

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מערכת בדיקת איכות מזון</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex; justify-content: center; align-items: center; direction: rtl;
        }
        .container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 90%; max-width: 400px; }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; font-size: 1.8rem; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 600; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 1rem; transition: border 0.3s; }
        input:focus { outline: none; border-color: #667eea; }
        .btn { width: 100%; padding: 14px; background: #667eea; color: white; border: none; border-radius: 10px; font-size: 1.1rem; cursor: pointer; transition: background 0.3s; }
        .btn:hover { background: #5568d3; }
        .message { margin-top: 15px; padding: 10px; border-radius: 8px; text-align: center; }
        .error { background: #ffebee; color: #c62828; }
        .demo-info { margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 10px; font-size: 0.9rem; color: #666; }
        .demo-info strong { color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍽️ מערכת בדיקת איכות מזון</h1>
        <form method="POST" action="/login">
            <div class="form-group">
                <label>שם משתמש</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>סיסמה</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">התחבר</button>
            {% if error %}<div class="message error">{{ error }}</div>{% endif %}
        </form>
        <div class="demo-info">
            <strong>חשבונות לדוגמה:</strong><br><br>
            <strong>מטה:</strong> headquarters / admin123<br>
            <strong>מסעדה 1:</strong> restaurant1 / rest123<br>
            <strong>מסעדה 2:</strong> restaurant2 / rest123
        </div>
    </div>
</body>
</html>
"""

FORM_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>טופס בדיקת איכות</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; direction: rtl; }
        .header { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header h2 { color: #667eea; }
        .logout-btn { padding: 10px 20px; background: #e53e3e; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; }
        .container { background: white; padding: 40px; border-radius: 20px; max-width: 800px; margin: 0 auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; }
        .question { margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .question label { display: block; margin-bottom: 10px; font-weight: 600; color: #333; }
        .radio-group { display: flex; gap: 20px; }
        .radio-group label { display: flex; align-items: center; gap: 8px; font-weight: normal; }
        .rating { display: flex; gap: 10px; }
        .rating input[type="radio"] { display: none; }
        .rating label { padding: 10px 20px; background: #e0e0e0; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .rating input[type="radio"]:checked + label { background: #667eea; color: white; }
        textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 1rem; resize: vertical; min-height: 100px; }
        .submit-btn { width: 100%; padding: 16px; background: #48bb78; color: white; border: none; border-radius: 10px; font-size: 1.2rem; cursor: pointer; transition: background 0.3s; }
        .submit-btn:hover { background: #38a169; }
        .success { background: #c6f6d5; color: #22543d; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
        .nav { display: flex; gap: 10px; }
        .nav a { padding: 10px 20px; background: #667eea; color: white; border-radius: 8px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h2>שלום, {{ user_name }}</h2>
        <div class="nav">
            <a href="/results">תוצאות</a>
            <a href="/logout" class="logout-btn">יציאה</a>
        </div>
    </div>
    <div class="container">
        <h1>טופס בדיקת איכות מזון</h1>
        {% if success %}<div class="success">✅ הטופס נשלח בהצלחה!</div>{% endif %}
        <form method="POST" action="/submit-form">
            {% for q in questions %}
            <div class="question">
                <label>{{ q.question }}</label>
                {% if q.type == 'yesno' %}
                <div class="radio-group">
                    <label><input type="radio" name="{{ q.id }}" value="yes" required> כן</label>
                    <label><input type="radio" name="{{ q.id }}" value="no" required> לא</label>
                </div>
                {% elif q.type == 'rating' %}
                <div class="rating">
                    {% for i in range(1, 6) %}
                    <input type="radio" name="{{ q.id }}" value="{{ i }}" id="{{ q.id }}_{{ i }}" required>
                    <label for="{{ q.id }}_{{ i }}">{{ i }}</label>
                    {% endfor %}
                </div>
                {% elif q.type == 'text' %}
                <textarea name="{{ q.id }}"></textarea>
                {% endif %}
            </div>
            {% endfor %}
            <button type="submit" class="submit-btn">שלח טופס</button>
        </form>
    </div>
</body>
</html>
"""

RESULTS_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>תוצאות בדיקות</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; direction: rtl; }
        .header { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .nav { display: flex; gap: 10px; }
        .nav a { padding: 10px 20px; background: #667eea; color: white; border-radius: 8px; text-decoration: none; }
        .logout-btn { padding: 10px 20px; background: #e53e3e; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; }
        .container { background: white; padding: 40px; border-radius: 20px; max-width: 1200px; margin: 0 auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; }
        .submission { border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .submission-header { display: flex; justify-content: space-between; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 2px solid #f0f0f0; }
        .submission-header strong { color: #667eea; }
        .answer { margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .empty { text-align: center; color: #999; padding: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>שלום, {{ user_name }}</h2>
        <div class="nav">
            <a href="/form">טופס חדש</a>
            <a href="/logout" class="logout-btn">יציאה</a>
        </div>
    </div>
    <div class="container">
        <h1>תוצאות בדיקות איכות</h1>
        {% if submissions %}
            {% for sub in submissions %}
            <div class="submission">
                <div class="submission-header">
                    <div><strong>מסעדה:</strong> {{ sub.restaurant }}<br><strong>מבצע הבדיקה:</strong> {{ sub.inspector }}</div>
                    <div><strong>תאריך:</strong> {{ sub.timestamp }}</div>
                </div>
                {% for key, value in sub.answers.items() %}
                <div class="answer"><strong>{{ key }}:</strong> {{ value }}</div>
                {% endfor %}
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">אין עדיין בדיקות שנשלחו</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('form_page'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']
        session['name'] = USERS[username]['name']
        return redirect(url_for('form_page'))
    return render_template_string(LOGIN_HTML, error="שם משתמש או סיסמה שגויים")

@app.route('/form')
def form_page():
    if 'username' not in session:
        return redirect(url_for('home'))
    success = request.args.get('success') == 'true'
    return render_template_string(FORM_HTML, questions=QUALITY_QUESTIONS, user_name=session['name'], success=success)

@app.route('/submit-form', methods=['POST'])
def submit_form():
    if 'username' not in session:
        return redirect(url_for('home'))
    answers = {}
    for question in QUALITY_QUESTIONS:
        answers[question['question']] = request.form.get(question['id'], '')
    submission = {
        'restaurant': session['name'],
        'inspector': session['username'],
        'role': session['role'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'answers': answers
    }
    submissions.append(submission)
    return redirect(url_for('form_page', success='true'))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('home'))
    if session['role'] == 'headquarters':
        filtered_submissions = submissions
    else:
        filtered_submissions = [s for s in submissions if s['restaurant'] == session['name']]
    return render_template_string(RESULTS_HTML, submissions=filtered_submissions, user_name=session['name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/status')
def status():
    return jsonify({"status": "running", "message": "Food Quality Management System", "version": "1.0.0", "total_submissions": len(submissions)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
