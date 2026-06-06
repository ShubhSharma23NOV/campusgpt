# CampusGPT – Complete Setup Guide

## ❌ Problem
Python 3.14 is too new. `pydantic-core` (used by FastAPI) needs pre-built wheels
which only exist for Python 3.8–3.12. Python 3.14 requires Visual Studio C++ Build
Tools to compile from source — which most users don't have installed.

## ✅ Fix: Install Python 3.12 (takes 2 minutes)

### Step 1 — Download Python 3.12
👉 https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe

Click that link, download, run the installer.
✅ Check "Add python.exe to PATH"
✅ Check "Install for all users" (optional)

### Step 2 — Verify
Open a NEW terminal (close this one first):
```
python --version   → should show Python 3.12.x
```

### Step 3 — Run the backend
```
cd C:\Users\karti\Desktop\campusGPT\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload
```

### Step 4 — Run the frontend (in a second terminal)
```
cd C:\Users\karti\Desktop\campusGPT\frontend
copy .env.example .env.local
npm run dev
```

### Step 5 — Open in browser
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/api/docs

### Login Credentials
| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Student | arjun@campusgpt.edu      | student123  |
| Student | priya@campusgpt.edu      | student123  |
| Admin   | admin@campusgpt.edu      | admin123    |

---

## Optional: Add Gemini AI
Edit `backend/.env` and set:
```
GEMINI_API_KEY=your_key_here
```
Get a free key at: https://aistudio.google.com/app/apikey
