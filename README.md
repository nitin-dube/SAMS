# Student Attendance Management System (SAMS)

A full‑stack web app for managing student attendance with role‑based views for students and faculty. Backend is Flask with Firestore; frontend is React.

## Tech stack
- Backend: Flask, Firebase Admin (Firestore), ReportLab
- Frontend: React (CRA), React Router

## Repository layout
```
SAMS/
  backend/backend-login-main/        # Flask API
  frontend/sam_working/              # React app
```

## Prerequisites
- Python 3.10+ and pip
- Node.js 18+ and npm
- Firebase project + Service Account JSON (Firestore enabled)
- Email account (Gmail App Password) for OTP/alerts

## Environment variables (required)
Set these before running the backend:
- GOOGLE_APPLICATION_CREDENTIALS: Absolute path to your Firebase service account JSON
- EMAIL_ADDRESS: Email used to send OTP/notifications
- EMAIL_PASSWORD: Email app password (never commit this)
- ALLOWED_ORIGINS: Comma‑separated list (e.g., http://localhost:3000,https://your-domain)
- PORT: Backend port (default 5000)
- ENABLE_STARTUP_TEST: 1 to write a connectivity doc to Firestore on start, else 0

## Run locally (development)
1) Backend
```powershell
cd backend/backend-login-main
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\\path\\to\\service_account.json"
$env:EMAIL_ADDRESS="your@gmail.com"
$env:EMAIL_PASSWORD="your_app_password"
$env:ALLOWED_ORIGINS="http://localhost:3000"
$env:PORT="5000"
py -3 -m pip install -r requirements.txt
py -3 app.py
```
Health check: http://127.0.0.1:5000/api/ping

2) Frontend
```powershell
cd frontend/sam_working
npm install
npm start
```
App: http://localhost:3000/SAMS

## Production build
Frontend build
```powershell
cd frontend/sam_working
npm run build
```
Serve the `frontend/sam_working/build/` directory with NGINX/IIS/Apache. Ensure the app base path `/SAMS` is preserved or update your server config accordingly.

Backend (production flags already set)
```powershell
cd backend/backend-login-main
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\\path\\to\\service_account.json"
$env:EMAIL_ADDRESS="your@gmail.com"
$env:EMAIL_PASSWORD="your_app_password"
$env:ALLOWED_ORIGINS="https://your-domain"
$env:PORT="5000"
py -3 app.py
```
For Windows services or IIS, prefer a process manager (e.g., NSSM) or a WSGI server (waitress) behind a reverse proxy.

## Security notes
- Do not commit service account JSON or passwords. They are read from env vars.
- Passwords in Firestore are plaintext (demo). If you later upgrade, use hashing (bcrypt) and protect sensitive routes.

## Common endpoints
- GET /api/ping – health check
- GET /api/dbtest – Firestore connectivity test (reads a doc)
- Attendance: POST /api/mark-attendance, GET /api/get-attendance, GET /api/student-attendance, GET /api/attendance-report, PDF downloads
- Users: POST /api/login, POST /api/forgot-password, POST /api/add-faculty, etc.

## GitHub repository setup
Initialize (if not already) and push to your GitHub repo. Replace placeholders with your values.
```powershell
cd C:\Users\NITIN DUBEY\Documents\SAMS
# If this repo is already initialized, you can skip git init
git init
# Ensure .gitignore is respected
git add .
git commit -m "Initial SAMS commit"
# Create a new repo on GitHub named SAMS (or any name), then set the remote:
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
# First push
git push -u origin main
```
If the remote already exists, update it:
```powershell
git remote set-url origin https://github.com/<your-username>/<your-repo>.git
```

## License
Add your preferred license (MIT recommended for open source).