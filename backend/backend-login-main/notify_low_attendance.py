import os
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.message import EmailMessage
from collections import defaultdict

db = None

def init_firebase():
    global db
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "sams-700c6-firebase-adminsdk-fbsvc-c90fa40430.json"))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

# Email credentials via environment
Email_Address = os.getenv("EMAIL_ADDRESS")
Email_Password = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = Email_Address
    msg["To"] = to_email

    if not Email_Address or not Email_Password:
        raise RuntimeError("Email credentials are not configured (EMAIL_ADDRESS/EMAIL_PASSWORD)")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(Email_Address, Email_Password)
        smtp.send_message(msg)
    print(f"Email sent to {to_email} with subject: {subject}")

def notify_students_from_attendance(threshold=75):
    if not db:
        init_firebase()
    attendance_ref = db.collection("attendance").stream()
    student_stats = defaultdict(lambda: {"present": 0, "total": 0})

    for doc in attendance_ref:
        data = doc.to_dict()
        records = data.get("records", {})
        for student_email, status in records.items():
            student_stats[student_email]["total"] += 1
            if str(status).strip().lower() == "present":
                student_stats[student_email]["present"] += 1

    # Get names from users collection
    users_ref = db.collection("users").stream()
    email_to_name = {}
    for user in users_ref:
        udata = user.to_dict()
        email_to_name[udata.get("email")] = udata.get("name", "Student")

    for student_email, stats in student_stats.items():
        total = stats["total"]
        present = stats["present"]
        attendance_percent = (present / total) * 100 if total > 0 else 0
        name = email_to_name.get(student_email, "Student")
        print(f"{name} ({student_email}): {attendance_percent:.2f}% attendance")
        if total > 0 and attendance_percent < threshold:
            message = (
                f"Dear {name},\n\n"
                f"Your current attendance is {attendance_percent:.2f}%. "
                f"This is below the required 75% minimum. "
                f"Please attend more classes to avoid penalties or being barred from exams.\n\n"
                f"- Faculty Team"
            )
            try:
                send_email(student_email, "Low Attendance Alert", message)
            except Exception as e:
                print(f"Failed to send email to {student_email}: {e}")

def update_student_fields():
    if not db:
        init_firebase()
    students = db.collection("students").stream()
    for student in students:
        data = student.to_dict()
        updates = {}
        # If old field names exist, copy values to new fields
        if "totalClasses" in data and "total_classes" not in data:
            updates["total_classes"] = data["totalClasses"]
        if "attended" in data and "attended_classes" not in data:
            updates["attended_classes"] = data["attended"]
        # You can add more mappings if needed
        if updates:
            db.collection("students").document(student.id).update(updates)
            print(f"Updated {student.id} with {updates}")

if __name__ == "__main__":
    init_firebase()
    notify_students_from_attendance()
    update_student_fields()
