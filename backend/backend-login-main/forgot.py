import smtplib
from email.message import EmailMessage
import random
import getpass

# -----------------------------------
# CONFIGURATION (edit this section only)
email_sender = 'attendancemanagementsysten@gmail.com'
email_password = 'wycaviyrlztaimew'  # App Password (keep secret!)
email_receivers = ['barnwalgourav680@gmail.com', 'rajuy5224@gmail.com', 'warishamanullah@gmail.com']  # ✅ multiple emails

# -----------------------------------
# Function to generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# -----------------------------------
# Function to send OTP to multiple recipients
def send_otp_via_email(receiver_emails, otp, sender_email, sender_password):
    subject = "Your OTP Code"
    body = f"Your OTP for password reset is: {otp}"

    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print("✅ OTP email sent to:", ", ".join(receiver_emails))
    except Exception as e:
        print(f"❌ Failed to send OTP email: {e}")

# -----------------------------------
# Function to handle password reset
def reset_password():
    otp = generate_otp()
    send_otp_via_email(email_receivers, otp, email_sender, email_password)

    user_otp = input("Enter the OTP received: ")
    if user_otp == otp:
        new_password = getpass.getpass("Enter your new password: ")
        confirm_password = getpass.getpass("Confirm your new password: ")

        if new_password == confirm_password:
            print("🎉 Password reset successful!")
        else:
            print("❗ Passwords do not match.")
    else:
        print("❌ Invalid OTP. Password reset failed.")

# -----------------------------------
# Run the reset process
reset_password()
