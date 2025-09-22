# Student Attendance Management System (SAMS)

A full‑stack web app for managing student attendance with role‑based views for students and faculty. Backend is Flask with Firestore; frontend is React.

## Features
- Student/faculty login (demo flow)
- Mark attendance per course/date (faculty)
- Student views: monthly/recent attendance, course‑wise stats
- Reports: course/date range reports, student PDF downloads
- Queries module: submit, list, update status, delete (demo)
- Email notifications for low attendance (via env‑configured SMTP)

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

Example (PowerShell):
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\\secrets\\service_account.json"
$env:EMAIL_ADDRESS="your@gmail.com"
$env:EMAIL_PASSWORD="your_app_password"
$env:ALLOWED_ORIGINS="http://localhost:3000,https://your-domain"
$env:PORT="5000"
$env:ENABLE_STARTUP_TEST="0"
```

## Run locally (development)
1) Backend
```powershell
cd backend/backend-login-main
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
py -3 app.py
```
For Windows services or IIS, prefer a process manager (e.g., NSSM) or a WSGI server (waitress) behind a reverse proxy.

### Example NGINX snippet (reverse proxy)
```
server {
  listen 80;
  server_name your-domain;

  location /api/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location /SAMS/ {
    root /var/www/sams-frontend; # contains the build folder
    try_files $uri $uri/ /SAMS/index.html;
  }
}
```

## Security notes
- Do not commit service account JSON or passwords. They are read from env vars.
- Passwords in Firestore are plaintext (demo). If you later upgrade, use hashing (bcrypt) and protect sensitive routes.

## Common endpoints
- GET /api/ping – health check
- GET /api/dbtest – Firestore connectivity test (reads a doc)
- Attendance: POST /api/mark-attendance, GET /api/get-attendance, GET /api/student-attendance, GET /api/attendance-report, PDF downloads
- Users: POST /api/login, POST /api/forgot-password, POST /api/add-faculty, etc.

## Troubleshooting
- Frontend cannot reach backend: ensure backend is on 5000 and CORS `ALLOWED_ORIGINS` includes your frontend URL.
- Firestore errors: verify `GOOGLE_APPLICATION_CREDENTIALS` path and service account permissions.
- Email fails: check `EMAIL_ADDRESS`/`EMAIL_PASSWORD` and allow app passwords.
- React dev path: this app serves under `/SAMS`. When deploying, preserve that base path or adjust routing.

## GitHub repository setup
Initialize (if not already) and push to your GitHub repo. Replace placeholders with your values.
```powershell
cd C:\Users\NITIN DUBEY\Documents\SAMS
# If this repo is already initialized, you can skip git init
git init
git add .
git commit -m "Initial SAMS commit"
# Create a new repo on GitHub, then set the remote:
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
If the remote already exists, update it:
```powershell
git remote set-url origin https://github.com/<your-username>/<your-repo>.git
```

## Screenshots
Place your screenshots in `frontend/sam_working/public/screenshots/` and update the paths below if needed.

![Login](frontend/sam_working/public/screenshots/login.png)
![Student Dashboard](frontend/sam_working/public/screenshots/student-dashboard.png)
![Faculty Dashboard](frontend/sam_working/public/screenshots/faculty-dashboard.png)
![Reports](frontend/sam_working/public/screenshots/reports.png)

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.