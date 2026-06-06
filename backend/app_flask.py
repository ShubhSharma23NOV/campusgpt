"""
CampusGPT - Flask backend (Python 3.14 compatible, zero compilation)
Run with:  python app_flask.py
"""

import os
import json
import hashlib
import secrets
import sqlite3
from datetime import datetime, date, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from dotenv import load_dotenv

load_dotenv()

# ─── App Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"], supports_credentials=True)

app.config["JWT_SECRET_KEY"]            = os.getenv("SECRET_KEY", "campusgpt-dev-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"]  = timedelta(hours=2)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

jwt = JWTManager(app)

DB_PATH    = os.getenv("DB_PATH", "./campusgpt_flask.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "policies"), exist_ok=True)

# ─── DB Helper ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def check_pw(pw: str, hashed: str) -> bool:
    return hash_pw(pw) == hashed

# ─── DB Init ─────────────────────────────────────────────────────────────────
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        department TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        course TEXT NOT NULL,
        branch TEXT,
        semester INTEGER DEFAULT 1,
        year INTEGER DEFAULT 1,
        batch INTEGER NOT NULL,
        section TEXT,
        category TEXT DEFAULT 'general',
        is_hostel_student INTEGER DEFAULT 0,
        guardian_name TEXT,
        guardian_phone TEXT,
        is_active INTEGER DEFAULT 1,
        last_login TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        course TEXT NOT NULL,
        semester INTEGER NOT NULL,
        credits INTEGER DEFAULT 3,
        type TEXT DEFAULT 'theory'
    );

    CREATE TABLE IF NOT EXISTS attendance_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        academic_year TEXT NOT NULL,
        semester INTEGER NOT NULL,
        total_classes INTEGER DEFAULT 0,
        attended_classes INTEGER DEFAULT 0,
        UNIQUE(student_id, subject_id, academic_year),
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    );

    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        academic_year TEXT NOT NULL,
        fee_type TEXT NOT NULL,
        total_amount REAL NOT NULL,
        paid_amount REAL DEFAULT 0,
        discount_amount REAL DEFAULT 0,
        due_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fee_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        receipt_number TEXT UNIQUE NOT NULL,
        FOREIGN KEY(fee_id) REFERENCES fees(id)
    );

    CREATE TABLE IF NOT EXISTS hostel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_name TEXT NOT NULL,
        block TEXT,
        room_number TEXT NOT NULL,
        floor INTEGER,
        room_type TEXT NOT NULL,
        monthly_rent REAL NOT NULL,
        is_available INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS hostel_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        hostel_id INTEGER NOT NULL,
        allotment_date TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        total_fee REAL NOT NULL,
        paid_amount REAL DEFAULT 0,
        next_due_date TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(hostel_id) REFERENCES hostel(id)
    );

    CREATE TABLE IF NOT EXISTS scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        application_start TEXT,
        application_end TEXT,
        academic_year TEXT NOT NULL,
        min_attendance REAL DEFAULT 75,
        description TEXT,
        categories_eligible TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS scholarship_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        scholarship_id INTEGER NOT NULL,
        status TEXT DEFAULT 'submitted',
        approved_amount REAL,
        applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, scholarship_id),
        FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS fines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        fine_type TEXT NOT NULL,
        reason TEXT NOT NULL,
        amount REAL NOT NULL,
        paid_amount REAL DEFAULT 0,
        fine_date TEXT NOT NULL,
        due_date TEXT,
        imposed_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        user_type TEXT DEFAULT 'student',
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        action_url TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        summary TEXT,
        is_active INTEGER DEFAULT 1,
        uploaded_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    # Seed if empty
    existing = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if existing == 0:
        seed_data(c)
        conn.commit()
        print("✅ Demo data seeded")

    conn.close()
    print(f"✅ Database ready at {DB_PATH}")


def seed_data(c):
    # Admins
    c.execute("INSERT INTO admins (name,email,password_hash,role,department) VALUES (?,?,?,?,?)",
              ("Super Admin","admin@campusgpt.edu", hash_pw("admin123"), "super_admin","Administration"))
    admin_id = c.lastrowid

    # Students
    pw = hash_pw("student123")
    c.execute("""INSERT INTO students
        (student_id,name,email,password_hash,phone,course,branch,semester,year,batch,section,category,is_hostel_student,guardian_name)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("2024CS001","Arjun Sharma","arjun@campusgpt.edu",pw,"9876543210",
         "B.Tech CSE","Computer Science",3,2,2024,"A","general",1,"Rajesh Sharma"))
    arjun_id = c.lastrowid

    c.execute("""INSERT INTO students
        (student_id,name,email,password_hash,phone,course,branch,semester,year,batch,section,category,is_hostel_student)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("2024CS002","Priya Singh","priya@campusgpt.edu",pw,"9876543211",
         "B.Tech CSE","Computer Science",3,2,2024,"A","obc",0))
    priya_id = c.lastrowid

    # Subjects
    subjects = [
        ("CS301","Data Structures & Algorithms","B.Tech CSE",3,4,"theory"),
        ("CS302","Database Management Systems","B.Tech CSE",3,4,"theory"),
        ("CS303","Operating Systems","B.Tech CSE",3,3,"theory"),
        ("CS304","DBMS Lab","B.Tech CSE",3,2,"lab"),
        ("CS305","Web Technologies","B.Tech CSE",3,3,"elective"),
    ]
    c.executemany("INSERT INTO subjects (code,name,course,semester,credits,type) VALUES (?,?,?,?,?,?)", subjects)
    sub_ids = [c.execute("SELECT id FROM subjects WHERE code=?", (s[0],)).fetchone()[0] for s in subjects]

    # Attendance summaries for Arjun (below 75% in some)
    att = [
        (arjun_id, sub_ids[0], "2024-25", 3, 40, 29),
        (arjun_id, sub_ids[1], "2024-25", 3, 38, 26),
        (arjun_id, sub_ids[2], "2024-25", 3, 36, 30),
        (arjun_id, sub_ids[3], "2024-25", 3, 20, 18),
        (arjun_id, sub_ids[4], "2024-25", 3, 35, 25),
        (priya_id, sub_ids[0], "2024-25", 3, 40, 38),
        (priya_id, sub_ids[1], "2024-25", 3, 38, 35),
    ]
    c.executemany("INSERT INTO attendance_summary (student_id,subject_id,academic_year,semester,total_classes,attended_classes) VALUES (?,?,?,?,?,?)", att)

    # Fees
    fees = [
        (arjun_id,"2024-25","tuition",85000,42500,0,"2025-01-15"),
        (arjun_id,"2024-25","hostel",36000,18000,0,"2025-01-15"),
        (arjun_id,"2024-25","exam",2500,2500,0,"2024-11-30"),
        (priya_id,"2024-25","tuition",85000,85000,0,"2024-11-15"),
    ]
    c.executemany("INSERT INTO fees (student_id,academic_year,fee_type,total_amount,paid_amount,discount_amount,due_date) VALUES (?,?,?,?,?,?,?)", fees)

    # Hostel
    c.execute("INSERT INTO hostel (hostel_name,block,room_number,floor,room_type,monthly_rent) VALUES (?,?,?,?,?,?)",
              ("Boys Hostel A","Block-1","101",1,"double",3000))
    hostel_id = c.lastrowid
    c.execute("INSERT INTO hostel_allocations (student_id,hostel_id,allotment_date,academic_year,total_fee,paid_amount,next_due_date,status) VALUES (?,?,?,?,?,?,?,?)",
              (arjun_id, hostel_id,"2024-07-15","2024-25",36000,18000,"2025-01-15","active"))

    # Scholarships
    c.execute("INSERT INTO scholarships (name,type,amount,application_start,application_end,academic_year,min_attendance,description) VALUES (?,?,?,?,?,?,?,?)",
              ("Merit Scholarship 2024","merit",25000,"2024-09-01","2024-10-31","2024-25",75,"For students with 80%+ marks"))
    sch_id = c.lastrowid
    c.execute("INSERT INTO scholarships (name,type,amount,application_start,application_end,academic_year,min_attendance,categories_eligible,description) VALUES (?,?,?,?,?,?,?,?,?)",
              ("SC/ST Government Scholarship","government",50000,"2024-08-01","2024-09-30","2024-25",75,'["sc","st"]',"Government scholarship for SC/ST"))

    # Application for Priya
    c.execute("INSERT INTO scholarship_applications (student_id,scholarship_id,status,approved_amount) VALUES (?,?,?,?)",
              (priya_id, sch_id,"approved",25000))

    # Fine for Arjun
    c.execute("INSERT INTO fines (student_id,fine_type,reason,amount,paid_amount,fine_date,due_date,imposed_by) VALUES (?,?,?,?,?,?,?,?)",
              (arjun_id,"library","Overdue library book – Introduction to Algorithms (15 days)",150,0,"2024-11-10","2024-11-30",admin_id))

    # Notifications
    notifs = [
        (arjun_id,"student","attendance_shortage","⚠️ Attendance Warning",
         "Your attendance in Web Technologies is 71.4%. Attend 5 more classes to reach 75%.","/attendance"),
        (arjun_id,"student","fee_due","💳 Fee Payment Reminder",
         "Tuition fee of ₹42,500 is due on 15 Jan 2025.","/fees"),
        (arjun_id,"student","fine_reminder","📚 Library Fine Pending",
         "You have a pending library fine of ₹150 due on 30 Nov 2024.","/fines"),
    ]
    c.executemany("INSERT INTO notifications (user_id,user_type,type,title,message,action_url) VALUES (?,?,?,?,?,?)", notifs)

    # Demo policy
    c.execute("INSERT INTO policies (title,category,file_name,file_path,summary,uploaded_by) VALUES (?,?,?,?,?,?)",
              ("Attendance Policy 2024-25","attendance","attendance_policy.pdf","uploads/policies/attendance_policy.pdf",
               "Minimum 75% attendance required. Below 65% = detained.", admin_id))

    print("📋 Login: arjun@campusgpt.edu / student123")
    print("📋 Login: admin@campusgpt.edu  / admin123")


# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("user_type") != "admin":
            return jsonify({"detail": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return jsonify({"message": "CampusGPT API running", "version": "1.0.0", "docs": "/api/docs"})

@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.post("/api/v1/auth/login")
def login():
    data = request.json
    email     = data.get("email", "").lower().strip()
    password  = data.get("password", "")
    user_type = data.get("user_type", "student")

    conn = get_db()
    if user_type == "student":
        row = conn.execute("SELECT * FROM students WHERE email=? AND is_active=1", (email,)).fetchone()
        if not row or not check_pw(password, row["password_hash"]):
            conn.close()
            return jsonify({"detail": "Invalid email or password"}), 401
        conn.execute("UPDATE students SET last_login=? WHERE id=?", (datetime.utcnow().isoformat(), row["id"]))
        conn.commit()
        conn.close()

        access  = create_access_token(identity=str(row["id"]), additional_claims={"user_type":"student"})
        refresh = create_refresh_token(identity=str(row["id"]), additional_claims={"user_type":"student"})
        return jsonify({
            "access_token": access, "refresh_token": refresh, "token_type": "bearer",
            "user_type": "student",
            "user": {"id":row["id"],"student_id":row["student_id"],"name":row["name"],
                     "email":row["email"],"course":row["course"],"semester":row["semester"],"avatar_url":None}
        })
    else:
        row = conn.execute("SELECT * FROM admins WHERE email=? AND 1=1", (email,)).fetchone()
        if not row or not check_pw(password, row["password_hash"]):
            conn.close()
            return jsonify({"detail": "Invalid email or password"}), 401
        conn.close()
        access  = create_access_token(identity=str(row["id"]), additional_claims={"user_type":"admin"})
        refresh = create_refresh_token(identity=str(row["id"]), additional_claims={"user_type":"admin"})
        return jsonify({
            "access_token": access, "refresh_token": refresh, "token_type": "bearer",
            "user_type": "admin",
            "user": {"id":row["id"],"name":row["name"],"email":row["email"],"role":row["role"],"department":row["department"]}
        })


@app.post("/api/v1/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims   = get_jwt()
    token    = create_access_token(identity=identity, additional_claims={"user_type": claims.get("user_type")})
    return jsonify({"access_token": token, "token_type": "bearer"})


@app.get("/api/v1/auth/me")
@jwt_required()
def get_me():
    uid    = get_jwt_identity()
    claims = get_jwt()
    conn   = get_db()
    if claims.get("user_type") == "student":
        row = conn.execute("SELECT * FROM students WHERE id=?", (uid,)).fetchone()
        conn.close()
        if not row: return jsonify({"detail":"Not found"}), 404
        return jsonify({"id":row["id"],"student_id":row["student_id"],"name":row["name"],
                        "email":row["email"],"course":row["course"],"semester":row["semester"],
                        "batch":row["batch"],"section":row["section"],"category":row["category"],
                        "is_hostel_student":bool(row["is_hostel_student"]),"avatar_url":None})
    else:
        row = conn.execute("SELECT * FROM admins WHERE id=?", (uid,)).fetchone()
        conn.close()
        if not row: return jsonify({"detail":"Not found"}), 404
        return jsonify({"id":row["id"],"name":row["name"],"email":row["email"],"role":row["role"]})


# ── ATTENDANCE ────────────────────────────────────────────────────────────────
@app.get("/api/v1/attendance/my")
@jwt_required()
def my_attendance():
    uid   = int(get_jwt_identity())
    year  = request.args.get("academic_year", "2024-25")
    conn  = get_db()
    rows  = conn.execute("""
        SELECT a.*, s.code, s.name as subject_name, s.credits, s.type
        FROM attendance_summary a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id=? AND a.academic_year=?
    """, (uid, year)).fetchall()
    conn.close()

    subjects = []
    total_t = total_a = 0
    for r in rows:
        pct = round((r["attended_classes"]/r["total_classes"])*100, 2) if r["total_classes"] > 0 else 0
        total_t += r["total_classes"]
        total_a += r["attended_classes"]
        needed = 0
        if pct < 75 and r["total_classes"] > 0:
            x = (0.75 * r["total_classes"] - r["attended_classes"]) / 0.25
            needed = max(0, int(x)+1)
        subjects.append({
            "subject_id":r["subject_id"],"subject_code":r["code"],
            "subject_name":r["subject_name"],"credits":r["credits"],"type":r["type"],
            "total_classes":r["total_classes"],"attended_classes":r["attended_classes"],
            "percentage":pct,
            "status":"safe" if pct>=75 else ("warning" if pct>=65 else "critical"),
            "deficit":round(75-pct,2) if pct<75 else 0,
            "classes_needed_for_75":needed
        })

    overall_pct = round((total_a/total_t)*100,2) if total_t > 0 else 0
    return jsonify({
        "academic_year": year,
        "overall":{
            "total_classes":total_t,"attended_classes":total_a,"percentage":overall_pct,
            "status":"safe" if overall_pct>=75 else ("warning" if overall_pct>=65 else "critical")
        },
        "subjects": subjects
    })


@app.get("/api/v1/attendance/my/trend")
@jwt_required()
def att_trend():
    # Return mock daily trend (no daily table in lightweight schema)
    from datetime import timedelta
    today = date.today()
    trend = []
    import random
    random.seed(42)
    for i in range(30):
        d = today - timedelta(days=29-i)
        total = random.randint(3,5)
        present = random.randint(2,total)
        trend.append({"date":str(d),"total":total,"present":present,"percentage":round(present/total*100,1)})
    return jsonify({"days":30,"trend":trend})


# ── FEES ──────────────────────────────────────────────────────────────────────
@app.get("/api/v1/fees/my")
@jwt_required()
def my_fees():
    uid  = int(get_jwt_identity())
    year = request.args.get("academic_year","2024-25")
    conn = get_db()
    rows = conn.execute("SELECT * FROM fees WHERE student_id=? AND academic_year=?", (uid,year)).fetchall()

    total_billed = total_paid = total_remaining = 0
    fees_list = []
    for r in rows:
        net       = r["total_amount"] - r["discount_amount"]
        remaining = max(0, net - r["paid_amount"])
        total_billed    += net
        total_paid      += r["paid_amount"]
        total_remaining += remaining
        status = "paid" if remaining<=0 else ("partially_paid" if r["paid_amount"]>0 else "unpaid")

        # payments
        pays = conn.execute("SELECT * FROM fee_payments WHERE fee_id=? ORDER BY payment_date DESC", (r["id"],)).fetchall()
        fees_list.append({
            "id":r["id"],"fee_type":r["fee_type"],"total_amount":r["total_amount"],
            "discount_amount":r["discount_amount"],"net_amount":net,
            "paid_amount":r["paid_amount"],"remaining_amount":remaining,
            "due_date":r["due_date"],"status":status,
            "payments":[{"id":p["id"],"amount":p["amount"],"payment_date":p["payment_date"],
                         "payment_method":p["payment_method"],"receipt_number":p["receipt_number"]} for p in pays]
        })
    conn.close()
    pct = round((total_paid/total_billed)*100,1) if total_billed>0 else 0
    return jsonify({
        "academic_year":year,
        "summary":{
            "total_amount":total_billed,"total_paid":total_paid,"total_remaining":total_remaining,
            "total_installments":2,"installments_paid":1 if total_paid>0 else 0,
            "installments_remaining":1 if total_remaining>0 else 0,"percent_paid":pct
        },
        "fees":fees_list
    })


@app.get("/api/v1/fees/my/history")
@jwt_required()
def fee_history():
    uid  = int(get_jwt_identity())
    conn = get_db()
    rows = conn.execute("""
        SELECT fp.*, f.fee_type FROM fee_payments fp
        JOIN fees f ON fp.fee_id=f.id
        WHERE fp.student_id=? ORDER BY fp.payment_date DESC LIMIT 50
    """, (uid,)).fetchall()
    conn.close()
    return jsonify({"history":[dict(r) for r in rows]})


# ── HOSTEL ────────────────────────────────────────────────────────────────────
@app.get("/api/v1/hostel/my")
@jwt_required()
def my_hostel():
    uid  = int(get_jwt_identity())
    conn = get_db()
    row  = conn.execute("""
        SELECT ha.*, h.hostel_name, h.block, h.room_number, h.floor, h.room_type, h.monthly_rent
        FROM hostel_allocations ha JOIN hostel h ON ha.hostel_id=h.id
        WHERE ha.student_id=? AND ha.status='active'
    """, (uid,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"has_hostel":False,"message":"Not allocated a hostel room"})

    pays = conn.execute("""SELECT * FROM fee_payments WHERE student_id=? ORDER BY payment_date DESC LIMIT 1""",
                        (uid,)).fetchone()
    all_pays = conn.execute("""SELECT * FROM fee_payments WHERE student_id=? ORDER BY payment_date DESC LIMIT 12""",
                            (uid,)).fetchall()
    conn.close()

    remaining = max(0, row["total_fee"] - row["paid_amount"])
    return jsonify({
        "has_hostel":True,
        "hostel":{"hostel_name":row["hostel_name"],"block":row["block"],"room_number":row["room_number"],
                  "floor":row["floor"],"room_type":row["room_type"],"monthly_rent":row["monthly_rent"]},
        "allocation":{"id":row["id"],"allotment_date":row["allotment_date"],"academic_year":row["academic_year"],
                      "total_fee":row["total_fee"],"paid_amount":row["paid_amount"],"remaining_fee":remaining,
                      "next_due_date":row["next_due_date"],"status":row["status"]},
        "last_payment":dict(pays) if pays else None,
        "payment_history":[dict(p) for p in all_pays]
    })


# ── SCHOLARSHIPS ──────────────────────────────────────────────────────────────
@app.get("/api/v1/scholarships")
@jwt_required()
def list_scholarships():
    year = request.args.get("academic_year","2024-25")
    conn = get_db()
    rows = conn.execute("SELECT * FROM scholarships WHERE is_active=1 AND academic_year=?", (year,)).fetchall()
    conn.close()
    today = str(date.today())
    result = []
    for r in rows:
        is_open = bool(r["application_start"] and r["application_end"] and
                       r["application_start"] <= today <= r["application_end"])
        result.append({**dict(r), "is_open": is_open})
    return jsonify({"scholarships": result})


@app.get("/api/v1/scholarships/my")
@jwt_required()
def my_scholarships():
    uid  = int(get_jwt_identity())
    year = request.args.get("academic_year","2024-25")
    conn = get_db()

    # My applications
    apps = conn.execute("""
        SELECT sa.*, s.name as scholarship_name, s.type as scholarship_type, s.amount
        FROM scholarship_applications sa
        JOIN scholarships s ON sa.scholarship_id=s.id
        WHERE sa.student_id=?
    """, (uid,)).fetchall()

    total_received = sum(a["approved_amount"] or 0 for a in apps if a["status"]=="disbursed")

    # Check eligible ones not yet applied
    today = str(date.today())
    applied_ids = {a["scholarship_id"] for a in apps}
    all_schs = conn.execute("SELECT * FROM scholarships WHERE is_active=1 AND academic_year=?", (year,)).fetchall()

    # Get student attendance to check eligibility
    att = conn.execute("""
        SELECT SUM(attended_classes) as att, SUM(total_classes) as total
        FROM attendance_summary WHERE student_id=? AND academic_year=?
    """, (uid, year)).fetchone()
    overall_pct = round((att["att"]/att["total"])*100,1) if att and att["total"] else 0

    student = conn.execute("SELECT * FROM students WHERE id=?", (uid,)).fetchone()
    conn.close()

    eligible = []
    for s in all_schs:
        if s["id"] in applied_ids: continue
        if s["min_attendance"] and overall_pct < s["min_attendance"]: continue
        cats = json.loads(s["categories_eligible"]) if s["categories_eligible"] else None
        if cats and student["category"] not in cats: continue
        is_open = bool(s["application_start"] and s["application_end"] and
                       s["application_start"] <= today <= s["application_end"])
        eligible.append({**dict(s), "is_open": is_open})

    return jsonify({
        "applications":[{
            "application_id":a["id"],"scholarship_id":a["scholarship_id"],
            "scholarship_name":a["scholarship_name"],"scholarship_type":a["scholarship_type"],
            "requested_amount":a["amount"],"approved_amount":a["approved_amount"],
            "status":a["status"],"applied_date":a["applied_date"]
        } for a in apps],
        "total_received": total_received,
        "eligible_scholarships": eligible
    })


@app.post("/api/v1/scholarships/apply/<int:sch_id>")
@jwt_required()
def apply_scholarship(sch_id):
    uid  = int(get_jwt_identity())
    conn = get_db()
    existing = conn.execute("SELECT id FROM scholarship_applications WHERE student_id=? AND scholarship_id=?",
                            (uid, sch_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({"detail":"Already applied"}), 400
    conn.execute("INSERT INTO scholarship_applications (student_id,scholarship_id,status) VALUES (?,?,?)",
                 (uid, sch_id, "submitted"))
    conn.commit()
    lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return jsonify({"message":"Application submitted","application_id":lid}), 201


# ── FINES ─────────────────────────────────────────────────────────────────────
@app.get("/api/v1/fines/my")
@jwt_required()
def my_fines():
    uid  = int(get_jwt_identity())
    conn = get_db()
    rows = conn.execute("SELECT * FROM fines WHERE student_id=? ORDER BY fine_date DESC", (uid,)).fetchall()
    conn.close()
    total_amt = sum(r["amount"] for r in rows)
    total_paid = sum(r["paid_amount"] for r in rows)
    today = str(date.today())
    fines_list = []
    for r in rows:
        remaining = max(0, r["amount"] - r["paid_amount"])
        status = "paid" if remaining<=0 else ("partially_paid" if r["paid_amount"]>0 else "unpaid")
        is_overdue = bool(r["due_date"] and r["due_date"] < today and status != "paid")
        fines_list.append({
            "id":r["id"],"fine_type":r["fine_type"],"reason":r["reason"],
            "amount":r["amount"],"paid_amount":r["paid_amount"],"remaining_amount":remaining,
            "fine_date":r["fine_date"],"due_date":r["due_date"],"status":status,"is_overdue":is_overdue
        })
    return jsonify({
        "summary":{
            "total_fines":len(rows),"total_amount":total_amt,
            "total_paid":total_paid,"total_pending":total_amt-total_paid,
            "has_pending":(total_amt-total_paid)>0
        },
        "fines":fines_list
    })


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
@app.get("/api/v1/notifications/my")
@jwt_required()
def my_notifications():
    uid       = int(get_jwt_identity())
    unread    = request.args.get("unread_only","false").lower() == "true"
    conn      = get_db()
    q = "SELECT * FROM notifications WHERE user_id=? AND user_type='student'"
    if unread:
        q += " AND is_read=0"
    q += " ORDER BY created_at DESC LIMIT 20"
    rows      = conn.execute(q, (uid,)).fetchall()
    unread_ct = conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (uid,)).fetchone()[0]
    conn.close()
    return jsonify({
        "unread_count": unread_ct,
        "notifications": [dict(r) for r in rows]
    })


@app.post("/api/v1/notifications/<int:nid>/read")
@jwt_required()
def mark_read(nid):
    uid  = int(get_jwt_identity())
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (nid, uid))
    conn.commit()
    conn.close()
    return jsonify({"message":"Marked as read"})


@app.post("/api/v1/notifications/read-all")
@jwt_required()
def mark_all_read():
    uid  = int(get_jwt_identity())
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=? AND user_type='student'", (uid,))
    conn.commit()
    conn.close()
    return jsonify({"message":"All marked as read"})


# ── POLICIES ──────────────────────────────────────────────────────────────────
@app.get("/api/v1/policies")
def list_policies():
    cat  = request.args.get("category")
    conn = get_db()
    q = "SELECT * FROM policies WHERE is_active=1"
    params = []
    if cat:
        q += " AND category=?"
        params.append(cat)
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify({"policies":[{**dict(r),"is_indexed":False} for r in rows]})


@app.post("/api/v1/policies/upload")
@jwt_required()
def upload_policy():
    claims = get_jwt()
    if claims.get("user_type") != "admin":
        return jsonify({"detail":"Admin required"}), 403

    title    = request.form.get("title","")
    category = request.form.get("category","general")
    file     = request.files.get("file")

    if not file:
        return jsonify({"detail":"No file provided"}), 400

    safe_name = f"{category}_{title.replace(' ','_').lower()}_{secrets.token_hex(4)}.pdf"
    save_path = os.path.join(UPLOAD_DIR, "policies", safe_name)
    file.save(save_path)

    conn = get_db()
    conn.execute("INSERT INTO policies (title,category,file_name,file_path,uploaded_by) VALUES (?,?,?,?,?)",
                 (title, category, file.filename, save_path, int(get_jwt_identity())))
    conn.commit()
    conn.close()
    return jsonify({"message":"Policy uploaded","chunks_indexed":0,"indexed":False}), 201


# ── AI CHAT ───────────────────────────────────────────────────────────────────
_sessions = {}   # in-memory chat sessions

def gemini_chat(question: str, context: str = "", history: list = None) -> str:
    """Call Gemini API if key set, otherwise return smart mock answers."""
    api_key = os.getenv("GEMINI_API_KEY","")

    if api_key and api_key != "your-gemini-api-key-here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            system = """You are CampusGPT, an AI assistant for college students.
Answer ONLY based on the context provided. If answer not found, say exactly:
'This information is not available in the uploaded policy documents.'
Be concise and cite the source."""

            prompt = f"{system}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    # Smart mock responses when no API key
    q = question.lower()
    if "attendance" in q and ("minimum" in q or "required" in q or "75" in q):
        return "📋 **Attendance Policy**: The minimum required attendance is **75%** in each subject. Students falling below 75% will not be allowed to appear in semester examinations. Students with attendance between 65-74% may apply for condonation with valid reasons.\n\n*Source: Attendance Policy 2024-25*"
    if "hostel" in q and ("tim" in q or "rule" in q or "curfew" in q):
        return "🏠 **Hostel Rules**: \n- Entry/exit timing: 6:00 AM – 10:00 PM\n- Night out requires prior written permission\n- Visitors allowed 4:00 PM – 7:00 PM only\n- Ragging, smoking, and alcohol are strictly prohibited\n\n*Source: Hostel Rules & Regulations*"
    if "scholarship" in q and ("apply" in q or "how" in q or "eligible" in q):
        return "🏆 **Scholarship Process**:\n1. Visit the scholarship portal during the application window\n2. Fill the online form with required documents\n3. Submit income certificate, marksheets, and identity proof\n4. Maintain minimum 75% attendance\n5. Merit scholarships require 80%+ academic marks\n\n*Source: Scholarship Guidelines 2024-25*"
    if "exam" in q and ("eligib" in q or "sit" in q or "appear" in q):
        return "📝 **Exam Eligibility**: Students must have:\n- Minimum **75% attendance** in each subject\n- No pending dues/fines\n- Completed all internal assessments\n- Valid enrollment\n\nStudents below 65% attendance are **detained** and cannot appear.\n\n*Source: Examination Rules*"
    if "fine" in q or "penalt" in q:
        return "⚠️ **Fine/Penalty Rules**:\n- Late fee payment: ₹50/day after due date\n- Library overdue: ₹10/day per book\n- Property damage: Cost + 20% penalty\n- Disciplinary violations: ₹500–₹5000 based on severity\n\n*Source: Student Conduct Policy*"
    if "fee" in q and ("structure" in q or "amount" in q or "cost" in q):
        return "💰 **Fee Structure 2024-25**:\n- Tuition Fee: ₹85,000/year (B.Tech)\n- Hostel Fee: ₹36,000/year\n- Exam Fee: ₹2,500/semester\n- Lab Fee: ₹3,000/year\n\nPayable in 2 installments. Late payment incurs ₹50/day penalty.\n\n*Source: Fee Structure 2024-25*"
    if "hello" in q or "hi " in q or q.strip() in ["hi","hello","hey"]:
        return "👋 Hello! I'm CampusGPT, your AI campus assistant. I can answer questions about:\n- 📋 Attendance policies\n- 🏠 Hostel rules\n- 💰 Fee structure\n- 📝 Examination rules\n- 🏆 Scholarship guidelines\n\nWhat would you like to know?"

    return "This information is not available in the uploaded policy documents. Please contact the administration office or check the official college website for more details."


@app.post("/api/v1/ai/chat")
def ai_chat():
    data       = request.json or {}
    question   = data.get("question","").strip()
    session_id = data.get("session_id") or secrets.token_hex(8)
    mode       = data.get("mode","policy")

    if not question:
        return jsonify({"detail":"Question cannot be empty"}), 400

    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]

    # For personalized mode, fetch student data
    context = ""
    claims  = {}
    auth_header = request.headers.get("Authorization","")
    if auth_header.startswith("Bearer "):
        try:
            from flask_jwt_extended import decode_token
            token_data = decode_token(auth_header[7:])
            uid = int(token_data["sub"])
            claims = token_data
        except:
            uid = None
    else:
        uid = None

    if mode == "personalized" and uid:
        conn = get_db()
        stu  = conn.execute("SELECT * FROM students WHERE id=?", (uid,)).fetchone()
        att  = conn.execute("""SELECT a.*, s.name FROM attendance_summary a
                                JOIN subjects s ON a.subject_id=s.id WHERE a.student_id=?""", (uid,)).fetchall()
        fees = conn.execute("SELECT * FROM fees WHERE student_id=?", (uid,)).fetchall()
        fines= conn.execute("SELECT * FROM fines WHERE student_id=?", (uid,)).fetchall()
        conn.close()

        if stu:
            context = f"Student: {stu['name']} | {stu['course']} Sem {stu['semester']}\n"
            if att:
                context += "ATTENDANCE:\n"
                for a in att:
                    pct = round(a['attended_classes']/a['total_classes']*100,1) if a['total_classes']>0 else 0
                    context += f"  - {a['name']}: {a['attended_classes']}/{a['total_classes']} = {pct}%\n"
            if fees:
                context += "FEES:\n"
                for f in fees:
                    remaining = max(0, f['total_amount']-f['paid_amount'])
                    context += f"  - {f['fee_type'].title()}: Paid ₹{f['paid_amount']} / ₹{f['total_amount']}, Remaining: ₹{remaining}, Due: {f['due_date']}\n"
            pending_fines = [f for f in fines if f['paid_amount']<f['amount']]
            if pending_fines:
                context += "PENDING FINES:\n"
                for f in pending_fines:
                    context += f"  - {f['reason']}: ₹{f['amount']-f['paid_amount']} remaining\n"

    import time
    start = time.time()
    answer = gemini_chat(question, context, history)
    elapsed = round(time.time()-start, 2)

    # Update session
    _sessions[session_id].append({"role":"user","content":question})
    _sessions[session_id].append({"role":"assistant","content":answer})
    if len(_sessions[session_id]) > 20:
        _sessions[session_id] = _sessions[session_id][-20:]

    return jsonify({
        "answer": answer,
        "sources": [{"title":"Campus Policy Documents","category":"general"}],
        "session_id": session_id,
        "was_answered": "not available" not in answer.lower(),
        "response_time": elapsed
    })


@app.get("/api/v1/ai/chat/history/<session_id>")
def chat_history(session_id):
    return jsonify({"session_id":session_id,"messages":_sessions.get(session_id,[])})


@app.delete("/api/v1/ai/chat/history/<session_id>")
def clear_chat(session_id):
    _sessions.pop(session_id, None)
    return jsonify({"message":"Cleared"})


@app.get("/api/v1/ai/attendance-advice")
@jwt_required()
def att_advice():
    uid  = int(get_jwt_identity())
    conn = get_db()
    rows = conn.execute("""
        SELECT a.*, s.name FROM attendance_summary a
        JOIN subjects s ON a.subject_id=s.id WHERE a.student_id=?
    """, (uid,)).fetchall()
    conn.close()

    subjects = []
    for r in rows:
        pct = round(r["attended_classes"]/r["total_classes"]*100,2) if r["total_classes"]>0 else 0
        subjects.append({"subject_name":r["name"],"attended":r["attended_classes"],
                         "total":r["total_classes"],"percentage":pct})

    # Build advice
    below = [s for s in subjects if s["percentage"] < 75]
    if not below:
        advice = "✅ Great job! Your attendance is above 75% in all subjects. Keep it up!"
    else:
        lines = [f"⚠️ Attendance Warning: {len(below)} subject(s) below 75%:"]
        for s in below:
            needed = max(0, int((0.75*s["total"]-s["attended"])/0.25)+1)
            lines.append(f"  📚 {s['subject_name']}: {s['percentage']:.1f}% → attend {needed} more classes")
        advice = "\n".join(lines)

    return jsonify({"advice":advice,"subjects":subjects})


# ── ADMIN ─────────────────────────────────────────────────────────────────────
@app.get("/api/v1/admin/dashboard")
@admin_required
def admin_dashboard():
    year = request.args.get("academic_year","2024-25")
    conn = get_db()

    total_stu  = conn.execute("SELECT COUNT(*) FROM students WHERE is_active=1").fetchone()[0]
    hostel_stu = conn.execute("SELECT COUNT(*) FROM students WHERE is_hostel_student=1").fetchone()[0]

    att = conn.execute("""SELECT AVG(CAST(attended_classes AS REAL)/total_classes*100) as avg,
                           SUM(CASE WHEN CAST(attended_classes AS REAL)/total_classes*100 < 75 THEN 1 ELSE 0 END) as below75
                           FROM attendance_summary WHERE academic_year=? AND total_classes>0""",(year,)).fetchone()

    fee = conn.execute("SELECT SUM(total_amount) as t, SUM(paid_amount) as p FROM fees WHERE academic_year=?",(year,)).fetchone()
    t_fee = fee["t"] or 0; p_fee = fee["p"] or 0

    fine = conn.execute("SELECT SUM(amount) as t, SUM(paid_amount) as p, COUNT(*) as cnt FROM fines").fetchone()

    sch = conn.execute("SELECT status, COUNT(*) as cnt FROM scholarship_applications GROUP BY status").fetchall()
    sch_dict = {r["status"]:r["cnt"] for r in sch}

    hostel_occ = conn.execute("SELECT COUNT(*) FROM hostel_allocations WHERE status='active'").fetchone()[0]
    conn.close()

    return jsonify({
        "students":{"total":total_stu,"hostel":hostel_stu,"day_scholars":total_stu-hostel_stu},
        "attendance":{
            "average_percentage":round(att["avg"] or 0, 2),
            "students_below_75": att["below75"] or 0
        },
        "fees":{
            "total_billed":t_fee,"total_collected":p_fee,
            "pending":t_fee-p_fee,
            "collection_rate":round((p_fee/t_fee)*100,2) if t_fee>0 else 0
        },
        "hostel":{"occupied_rooms":hostel_occ},
        "scholarships":{
            "submitted":sch_dict.get("submitted",0),"approved":sch_dict.get("approved",0),
            "disbursed":sch_dict.get("disbursed",0),"rejected":sch_dict.get("rejected",0)
        },
        "fines":{
            "total_amount":fine["t"] or 0,"collected":fine["p"] or 0,"total_count":fine["cnt"] or 0
        }
    })


@app.get("/api/v1/admin/analytics/attendance-distribution")
@admin_required
def att_distrib():
    year = request.args.get("academic_year","2024-25")
    conn = get_db()
    rows = conn.execute("""
        SELECT s.course, AVG(CAST(a.attended_classes AS REAL)/a.total_classes*100) as avg_attendance
        FROM attendance_summary a JOIN students s ON a.student_id=s.id
        WHERE a.academic_year=? AND a.total_classes>0
        GROUP BY s.course
    """, (year,)).fetchall()
    conn.close()
    return jsonify({"by_course":[{"course":r["course"],"average":round(r["avg_attendance"] or 0,2)} for r in rows]})


@app.get("/api/v1/admin/analytics/fee-collection")
@admin_required
def fee_collection():
    conn = get_db()
    rows = conn.execute("""
        SELECT strftime('%Y-%m', payment_date) as month,
               SUM(amount) as amount, COUNT(*) as transactions
        FROM fee_payments GROUP BY month ORDER BY month DESC LIMIT 12
    """).fetchall()
    conn.close()
    return jsonify({"monthly_trend":[dict(r) for r in rows]})


@app.get("/api/v1/students")
@admin_required
def list_students():
    conn = get_db()
    rows = conn.execute("SELECT * FROM students WHERE is_active=1 ORDER BY name LIMIT 100").fetchall()
    conn.close()
    return jsonify({"total":len(rows),"page":1,"limit":100,"pages":1,
                    "students":[dict(r) for r in rows]})


# ── STATIC UPLOADS ────────────────────────────────────────────────────────────
@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting CampusGPT Flask Server (Python 3.14 compatible)")
    print("=" * 55)
    init_db()
    print("\n✅ Server starting at http://localhost:8000")
    print("📋 Student login: arjun@campusgpt.edu / student123")
    print("🔑 Admin login:   admin@campusgpt.edu / admin123")
    print("=" * 55 + "\n")
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=True)
