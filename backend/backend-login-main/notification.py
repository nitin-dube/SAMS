import os
import smtplib
from email.mime_text import MIMEText

def send_email(student_email, student_name):
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    if not email_address or not email_password:
        raise RuntimeError('Email credentials are not configured (EMAIL_ADDRESS/EMAIL_PASSWORD)')
    msg = MIMEText(f"Dear {student_name},\nYour attendance is below 75%. Please take action.")
    msg['Subject'] = "Attendance Alert"
    msg['From'] = email_address
    msg['To'] = student_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)
        server.send_message(msg)
