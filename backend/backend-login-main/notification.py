import smtplib
from email.mime.text import MIMEText

def send_email(student_email, student_name):
    msg = MIMEText(f"Dear {student_name},\nYour attendance is below 75%. Please take action.")
    msg['Subject'] = "Attendance Alert"
    msg['From'] = "your_email@example.com"
    msg['To'] = student_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("your_email@example.com", "your_password")
        server.send_message(msg)
