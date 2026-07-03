# 🎓 CampusGPT – AI Student Copilot

> A full-stack AI-powered student platform built for hackathons and real campus use.  
> Ask questions in **Hindi, Hinglish, or English** — get instant answers from official college policy documents.

![CampusGPT Banner](https://img.shields.io/badge/CampusGPT-AI%20Student%20Copilot-blue?style=for-the-badge&logo=graduation-cap)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🤖 **AI Policy Navigator** | RAG chatbot answers questions from official PDF documents |
| 📊 **Student Dashboard** | Attendance, fees, hostel, scholarships & fines in one view |
| 📚 **Attendance Tracker** | Per-subject tracking with AI advice on how to reach 75% |
| 💰 **Fee Management** | Installment tracking, payment history, due date alerts |
| 🏠 **Hostel Management** | Room details, payment status, next due dates |
| 🏆 **Scholarship Tracker** | Eligibility checker and one-click application |
| ⚠️ **Fine Management** | Penalty tracking with status and overdue alerts |
| 🔔 **Notifications** | In-app alerts for attendance, fees, fines, deadlines |
| 🛡️ **Admin Panel** | Analytics dashboard, policy upload, student management |
| 🎙️ **Voice Support** | Speech-to-text input (browser Web Speech API) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (or Python 3.14 for Flask mode)
- Node.js 18+
- Git

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/campusGPT.git
cd campusGPT
```

### 2. Backend setup
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
# Edit .env → add your GEMINI_API_KEY

# Start server (works on Python 3.14 too)
python app_flask.py
```
Backend runs at → **http://localhost:8000**

### 3. Frontend setup
```bash
cd frontend
npm install
copy .env.example .env.local   # Windows
npm run dev
```
Frontend runs at → **http://localhost:5173**
   App working link:- https://campusgpt-ai-student-copilot-356200851822.asia-southeast1.run.app

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| 🎓 Student | `arjun@campusgpt.edu` | `student123` |
| 🎓 Student | `priya@campusgpt.edu` | `student123` |
| 🔑 Admin | `admin@campusgpt.edu` | `admin123` |

---

## 🤖 Enable Real Gemini AI

1. Get a **free API key** → https://aistudio.google.com/app/apikey
2. Edit `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```
3. Backend auto-reloads — no restart needed

Without a key, the app uses smart **mock responses** for demo purposes.

---

## 🏗️ Tech Stack

```
Frontend          Backend           AI / DB
─────────         ─────────         ────────
React 18          Flask 3.1         Gemini 1.5 Flash
Tailwind CSS      JWT Auth          ChromaDB (RAG)
Recharts          SQLite / MySQL    LangChain
Zustand           SQLAlchemy        Sentence Transformers
React Query       Python 3.11+      pypdf
Lucide Icons      REST API
```

---

## 📁 Project Structure

```
campusGPT/
├── backend/
│   ├── app/                  # FastAPI app (Python 3.11+)
│   │   ├── api/v1/           # Route handlers
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # AI/RAG service
│   │   └── core/             # Config, DB, Security
│   ├── app_flask.py          # Flask app (Python 3.14 compatible)
│   ├── init_db.py            # Database seeder
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # All page components
│   │   ├── components/       # Reusable UI components
│   │   ├── store/            # Zustand state management
│   │   └── lib/              # Axios API client
│   └── package.json
├── database/
│   ├── schema.sql            # MySQL schema
│   └── seed.sql              # Sample data
├── docker-compose.yml        # Full Docker setup
└── README.md
```

---

## 🐳 Docker (Full Stack)

```bash
# Copy and configure env
cp backend/.env.example backend/.env
# Add GEMINI_API_KEY to backend/.env

# Build and run everything
docker-compose up --build
```
Opens at → **http://localhost**

---

## 📸 Screenshots

| Landing Page | Student Dashboard |
|---|---|
| *AI-powered campus portal* | *Attendance, fees, fines overview* |

| AI Chat | Admin Analytics |
|---|---|
| *Policy questions in Hindi/English* | *Charts and statistics* |

---

## 🗺️ Roadmap

- [x] Core student dashboard
- [x] AI chat with RAG (PDF policies)
- [x] Attendance, fees, hostel, scholarships, fines
- [x] Admin panel with analytics
- [x] JWT authentication
- [ ] Email/SMS notifications
- [ ] Full MySQL production mode
- [ ] Mobile app (React Native)
- [ ] Exam timetable module
- [ ] Parent portal

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🏆 Built For

This project was built as a **hackathon prototype** demonstrating AI integration in campus management systems.

**Made with ❤️ using Gemini AI + React + Flask**
