from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseMode
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

app = FastAPI(title="Giraffe Quality System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def get_db():
    db = sqlite3.connect("giraffe_quality.db")
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            branch TEXT NOT NULL,
            role TEXT DEFAULT 'branch'
        )
    """)
    
    # Quality checks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            chef_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    """)
    
    # Insert default users
    branches = ["חיפה", "הרצליה", "רמהח", "פתח תקווה", "ראשלצ", "סביון", 
                "מודיעין", "לנדמרק", "נס ציונה", "מטה"]
    
    for branch in branches:
        try:
            if branch == "מטה":
                cursor.execute(
                    "INSERT INTO users (username, password, branch, role) VALUES (?, ?, ?, ?)",
                    (f"admin", "admin123", branch, "admin")
                )
            else:
                cursor.execute(
                    "INSERT INTO users (username, password, branch, role) VALUES (?, ?, ?, ?)",
                    (f"{branch}", "1234", branch, "branch")
                )
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    db.close()

init_db()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class QualityCheck(BaseModel):
    dish_name: str
    chef_name: str
    rating: int
    notes: Optional[str] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ג'ירף - איכויות מזון</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #000;
            font-size: 2rem;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #333;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5568d3;
        }
        .hidden {
            display: none;
        }
        .rating-input {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }
        .rating-btn {
            width: 50px;
            height: 50px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .rating-btn:hover {
            border-color: #667eea;
            transform: scale(1.1);
        }
        .rating-btn.selected {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            resize: vertical;
            min-height: 80px;
            font-family: inherit;
        }
        .success {
            background: #4caf50;
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }
        .logout-btn {
            background: #f44336;
            margin-top: 10px;
        }
        .logout-btn:hover {
            background: #d32f2f;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="loginForm">
            <h1>🍽️ ג'ירף מטבחים</h1>
            <p class="subtitle">מערכת איכויות מזון</p>
            <div class="input-group">
                <label>שם משתמש</label>
                <input type="text" id="username" placeholder="הזן שם משתמש">
            </div>
            <div class="input-group">
                <label>סיסמה</label>
                <input type="password" id="password" placeholder="הזן סיסמה">
            </div>
            <button onclick="login()">כניסה</button>
        </div>

        <div id="qualityForm" class="hidden">
            <h1>🍽️ טופס איכות מזון</h1>
            <p class="subtitle" id="branchName"></p>
            <div id="successMsg" class="success hidden">הטופס נשלח בהצלחה!</div>
            
            <div class="input-group">
                <label>שם המנה</label>
                <input type="text" id="dishName" list="dishes" placeholder="בחר או הקלד">
                <datalist id="dishes"></datalist>
            </div>
            
            <div class="input-group">
                <label>שם הטבח</label>
                <input type="text" id="chefName" list="chefs" placeholder="בחר או הקלד">
                <datalist id="chefs"></datalist>
            </div>
            
            <div class="input-group">
                <label>ציון המנה (1-10)</label>
                <div class="rating-input" id="ratingButtons"></div>
            </div>
            
            <div class="input-group">
                <label>הערות</label>
                <textarea id="notes" placeholder="הוסף הערות (אופציונלי)"></textarea>
            </div>
            
            <button onclick="submitQuality()">שלח טופס</button>
            <button class="logout-btn" onclick="logout()">התנתק</button>
        </div>
    </div>

    <script>
        let currentUser = null;
        let selectedRating = 0;

        // Create rating buttons
        for(let i = 1; i <= 10; i++) {
            const btn = document.createElement('button');
            btn.className = 'rating-btn';
            btn.textContent = i;
            btn.type = 'button';
            btn.onclick = () => selectRating(i);
            document.getElementById('ratingButtons').appendChild(btn);
        }

        function selectRating(rating) {
            selectedRating = rating;
            document.querySelectorAll('.rating-btn').forEach((btn, idx) => {
                btn.classList.toggle('selected', idx + 1 === rating);
            });
        }

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });

            if(response.ok) {
                currentUser = await response.json();
                document.getElementById('loginForm').classList.add('hidden');
                document.getElementById('qualityForm').classList.remove('hidden');
                document.getElementById('branchName').textContent = 'סניף: ' + currentUser.branch;
                loadDishes();
                loadChefs();
            } else {
                alert('שם משתמש או סיסמה שגויים');
            }
        }

        function logout() {
            currentUser = null;
            selectedRating = 0;
            document.getElementById('loginForm').classList.remove('hidden');
            document.getElementById('qualityForm').classList.add('hidden');
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }

        async function loadDishes() {
            const dishes = ['המבורגר', 'צ\'יפס', 'סלט', 'מרק', 'סטייק', 'דג', 'פסטה', 'פיצה'];
            const datalist = document.getElementById('dishes');
            dishes.forEach(dish => {
                const option = document.createElement('option');
                option.value = dish;
                datalist.appendChild(option);
            });
        }

        async function loadChefs() {
            const chefs = ['יוסי', 'דוד', 'משה', 'אבי', 'רון', 'אלי'];
            const datalist = document.getElementById('chefs');
            chefs.forEach(chef => {
                const option = document.createElement('option');
                option.value = chef;
                datalist.appendChild(option);
            });
        }

        async function submitQuality() {
            if(!selectedRating) {
                alert('נא לבחור ציון');
                return;
            }

            const data = {
                dish_name: document.getElementById('dishName').value,
                chef_name: document.getElementById('chefName').value,
                rating: selectedRating,
                notes: document.getElementById('notes').value
            };

            const response = await fetch('/api/quality-check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + currentUser.username
                },
                body: JSON.stringify(data)
            });

            if(response.ok) {
                document.getElementById('successMsg').classList.remove('hidden');
                document.getElementById('dishName').value = '';
                document.getElementById('chefName').value = '';
                document.getElementById('notes').value = '';
                selectedRating = 0;
                document.querySelectorAll('.rating-btn').forEach(btn => {
                    btn.classList.remove('selected');
                });
                setTimeout(() => {
                    document.getElementById('successMsg').classList.add('hidden');
                }, 3000);
            } else {
                alert('שגיאה בשליחת הטופס');
            }
        }
    </script>
</body>
</html>"""

@app.post("/api/login")
async def login(request: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (request.username, request.password)
    )
    user = cursor.fetchone()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "username": user["username"],
        "branch": user["branch"],
        "role": user["role"]
    }

@app.post("/api/quality-check")
async def create_quality_check(check: QualityCheck, authorization: str = Depends(lambda: None)):
    username = authorization.replace("Bearer ", "") if authorization else None
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT branch FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    cursor.execute("""
        INSERT INTO quality_checks (branch, dish_name, chef_name, rating, notes, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user["branch"],
        check.dish_name,
        check.chef_name,
        check.rating,
        check.notes,
        datetime.now().isoformat(),
        username
    ))
    
    db.commit()
    db.close()
    
    return {"status": "success", "id": cursor.lastrowid}

@app.get("/api/quality-checks")
async def get_quality_checks(branch: Optional[str] = None):
    db = get_db()
    cursor = db.cursor()
    
    if branch and branch != "מטה":
        cursor.execute(
            "SELECT * FROM quality_checks WHERE branch = ? ORDER BY created_at DESC",
            (branch,)
        )
    else:
        cursor.execute("SELECT * FROM quality_checks ORDER BY created_at DESC")
    
    checks = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return checks

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
