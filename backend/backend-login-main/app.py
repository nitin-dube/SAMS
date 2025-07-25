from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import random
import string
from flask import session
import os
import smtplib
from email.message import EmailMessage
import io
from reportlab.pdfgen import canvas
from notify_low_attendance import notify_students_from_attendance

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), 'firebase_service_account.json'))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Example: Test Firestore connection
try:
    test_ref = db.collection('test').document('connection')
    test_ref.set({'status': 'connected'})
    print('Successfully connected to Firestore!')
except Exception as e:
    print('Firestore connection failed:', e)

# Dummy credentials (replace with DB in real apps)
users = {
    'student1': 'pass123',
    'teacher1': 'teach456'
}

# In-memory OTP store for demo (use a persistent store in production)
otp_store = {}

def send_otp_email(to_email, otp):
    EMAIL_ADDRESS = 'attendancemanagementsysten@gmail.com'
    EMAIL_PASSWORD = 'wycaviyrlztaimew'
    msg = EmailMessage()
    msg['Subject'] = 'Your OTP for Password Reset'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f'Your OTP for password reset is: {otp}')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return f"Welcome, {username}!"
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'Connected!'})

@app.route('/api/dbtest', methods=['GET'])
def dbtest():
    doc = db.collection('test').document('connection').get()
    if doc.exists:
        return jsonify(doc.to_dict())
    else:
        return jsonify({'error': 'No document found'}), 404

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    courses = data.get('courses') or []
    if isinstance(courses, str):
        courses = [courses]
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        # For demo: compare plain text (in production, use hashed passwords!)
        if user_data.get('password') == password:
            # Name check: case sensitive for students, case insensitive for others
            if name:
                if 'name' not in user_data or not user_data['name']:
                    user_ref.update({'name': name})
                    user_data['name'] = name
                else:
                    if user_data.get('role') == 'student':
                        if name.strip() != user_data['name'].strip():
                            return jsonify({'success': False, 'error': 'Name does not match our records.'}), 401
                    else:
                        if name.strip().lower() != user_data['name'].strip().lower():
                            return jsonify({'success': False, 'error': 'Name does not match our records.'}), 401
            # Course logic: faculty must have pre-assigned courses, cannot set on login
            if courses:
                if user_data.get('role') == 'faculty':
                    # Faculty must have courses already assigned
                    if 'courses' not in user_data or not user_data['courses']:
                        return jsonify({'success': False, 'error': 'No courses assigned to this faculty. Contact admin.'}), 403
                    for course in courses:
                        if course.strip().lower() not in [c.strip().lower() for c in user_data['courses']]:
                            allowed_courses = ', '.join(user_data['courses'])
                            return jsonify({'success': False, 'error': f'You are not assigned to the course "{course}". Allowed courses: {allowed_courses}.'}), 403
                elif user_data.get('role') == 'student':
                    # For students, keep previous logic
                    if 'courses' not in user_data or not user_data['courses']:
                        user_ref.update({'courses': courses})
                        user_data['courses'] = courses
                    elif any(course.strip().lower() != c.strip().lower() for course in courses for c in user_data['courses']):
                        return jsonify({'success': False, 'error': 'Course does not match our records and cannot be changed.'}), 401
            user_data.pop('password', None)
            # Prepare response with all required fields
            response = {
                'success': True,
                'name': user_data.get('name'),
                'email': email,
                'courses': user_data.get('courses'),
                'role': user_data.get('role'),
                'low_attendance_alert': user_data.get('low_attendance_alert', False)
            }
            return jsonify(response)
        else:
            return jsonify({'success': False, 'error': 'Incorrect password'}), 401
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/list-users', methods=['GET'])
def list_users():
    users_ref = db.collection('users').stream()
    users_list = []
    for doc in users_ref:
        user = doc.to_dict()
        user['id'] = doc.id
        users_list.append(user)
    return jsonify(users_list)

@app.route('/api/set-faculty-name', methods=['POST'])
def set_faculty_name():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    if not email or not name:
        return jsonify({'success': False, 'error': 'Email and name required'}), 400
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user_data = user_doc.to_dict()
    if user_data.get('role') not in ['faculty', 'admin']:
        return jsonify({'success': False, 'error': 'Not a faculty or admin user'}), 403
    user_ref.update({'name': name})
    return jsonify({'success': True, 'message': f"Name updated for {email}"})

@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[email] = otp
    try:
        send_otp_email(email, otp)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to send email: {str(e)}'}), 500
    return jsonify({'success': True, 'message': 'OTP sent to your email.'})

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')
    otp = data.get('otp')
    if not email or not new_password or not otp:
        return jsonify({'success': False, 'error': 'Email, OTP, and new password required'}), 400
    if email not in otp_store or otp_store[email] != otp:
        return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 401
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user_ref.update({'password': new_password})
    del otp_store[email]
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/api/add-faculty', methods=['POST'])
def add_faculty():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    courses = data.get('courses') or []
    if isinstance(courses, str):
        courses = [courses]
    if not email or not password or not name:
        return jsonify({'success': False, 'error': 'Email, password, and name required'}), 400
    user_ref = db.collection('users').document(email)
    if user_ref.get().exists:
        return jsonify({'success': False, 'error': 'User already exists'}), 409
    user_ref.set({
        'email': email,
        'password': password,
        'name': name,
        'courses': courses,
        'role': 'faculty'
    })
    return jsonify({'success': True, 'message': f'Faculty {name} added.'})

@app.route('/api/update-faculty', methods=['POST'])
def update_faculty():
    data = request.get_json()
    email = data.get('email')
    courses = data.get('courses') or []
    if isinstance(courses, str):
        courses = [courses]
    if not email or not courses:
        return jsonify({'success': False, 'error': 'Email and courses required'}), 400
    user_ref = db.collection('users').document(email)
    if not user_ref.get().exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user_ref.update({'courses': courses})
    return jsonify({'success': True, 'message': f'Courses updated for {email}.'})

@app.route('/api/change-email', methods=['POST'])
def change_email():
    data = request.get_json()
    old_email = data.get('old_email')
    new_email = data.get('new_email')
    if not old_email or not new_email:
        return jsonify({'success': False, 'error': 'Old and new email required'}), 400
    user_ref = db.collection('users').document(old_email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'Old email not found'}), 404
    new_user_ref = db.collection('users').document(new_email)
    if new_user_ref.get().exists:
        return jsonify({'success': False, 'error': 'New email already exists'}), 409
    user_data = user_doc.to_dict()
    user_data['email'] = new_email
    new_user_ref.set(user_data)
    user_ref.delete()
    return jsonify({'success': True, 'message': f'Email changed from {old_email} to {new_email}.'})

@app.route('/api/set-password', methods=['POST'])
def set_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')
    if not email or not new_password:
        return jsonify({'success': False, 'error': 'Email and new password required'}), 400
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    user_ref.update({'password': new_password})
    return jsonify({'success': True, 'message': f'Password updated for {email}.'})

@app.route('/api/batch-update-student-courses', methods=['POST'])
def batch_update_student_courses():
    mapping = request.get_json()  # expects {email: courses, ...}
    updated = []
    not_found = []
    for email, courses in mapping.items():
        user_ref = db.collection('users').document(email)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            if user_data.get('role') == 'student':
                user_ref.update({'courses': courses})
                updated.append(email)
            else:
                not_found.append(email + ' (not a student)')
        else:
            not_found.append(email + ' (not found)')
    return jsonify({'updated': updated, 'not_found': not_found})

@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    course = data.get('course')
    date = data.get('date')
    attendance = data.get('attendance')
    faculty = data.get('faculty')
    if not course or not date or not attendance:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    doc_id = f'{course}_{date}'
    db.collection('attendance').document(doc_id).set({
        'course': course,
        'date': date,
        'marked_by': faculty,
        'records': attendance
    })

    # Update total_classes and attended_classes for each student
    for student_email, status in attendance.items():
        user_ref = db.collection('users').document(student_email)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            total_classes = user_data.get('total_classes', 0) + 1
            attended_classes = user_data.get('attended_classes', 0)
            if str(status).strip().lower() == 'present':
                attended_classes += 1
            user_ref.update({
                'total_classes': total_classes,
                'attended_classes': attended_classes
            })
    return jsonify({'success': True, 'message': 'Attendance recorded'})

@app.route('/api/get-attendance', methods=['GET'])
def get_attendance():
    course = request.args.get('course')
    date = request.args.get('date')
    if not course or not date:
        return jsonify({'success': False, 'error': 'Missing course or date'}), 400
    doc_id = f'{course}_{date}'
    doc = db.collection('attendance').document(doc_id).get()
    if not doc.exists:
        return jsonify({'success': False, 'error': 'No attendance found'}), 404
    return jsonify({'success': True, 'attendance': doc.to_dict()})

@app.route('/api/student-attendance', methods=['GET'])
def student_attendance():
    student = request.args.get('student')
    if not student:
        return jsonify({'success': False, 'error': 'Missing student'}), 400
    attendance_ref = db.collection('attendance').stream()
    history = []
    for doc in attendance_ref:
        data = doc.to_dict()
        records = data.get('records', {})
        if student in records:
            history.append({
                'course': data.get('course'),
                'date': data.get('date'),
                'status': records[student]
            })
    return jsonify({'success': True, 'history': history})

@app.route('/api/student-monthly-attendance', methods=['GET'])
def student_monthly_attendance():
    student = request.args.get('student')
    if not student:
        return jsonify({'success': False, 'error': 'Missing student'}), 400
    
    from datetime import datetime, timedelta
    import calendar
    
    # Calculate date range for past 1 month
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    last_month = first_day_of_month - timedelta(days=1)
    start_date = last_month.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    attendance_ref = db.collection('attendance').stream()
    monthly_history = []
    total_classes = 0
    present_count = 0
    absent_count = 0
    
    # For course-wise aggregation
    course_stats = {}
    
    for doc in attendance_ref:
        data = doc.to_dict()
        date = data.get('date')
        course = data.get('course')
        
        # Check if date is within the past month range
        if start_date <= date <= end_date:
            records = data.get('records', {})
            if student in records:
                status = records[student]
                monthly_history.append({
                    'course': course,
                    'date': date,
                    'status': status
                })
                total_classes += 1
                if status.lower() == 'present':
                    present_count += 1
                elif status.lower() == 'absent':
                    absent_count += 1
                # Aggregate per course
                if course not in course_stats:
                    course_stats[course] = {'total_classes': 0, 'presents': 0, 'absents': 0}
                course_stats[course]['total_classes'] += 1
                if status.lower() == 'present':
                    course_stats[course]['presents'] += 1
                elif status.lower() == 'absent':
                    course_stats[course]['absents'] += 1
    
    # Calculate attendance percentage
    attendance_percentage = round((present_count / total_classes * 100) if total_classes > 0 else 0, 1)
    
    # Sort by date (most recent first)
    monthly_history.sort(key=lambda x: x['date'], reverse=True)
    
    # Build course-wise attendance array
    course_wise_attendance = []
    for course, stats in course_stats.items():
        course_attendance_percentage = round((stats['presents'] / stats['total_classes'] * 100) if stats['total_classes'] > 0 else 0, 1)
        course_wise_attendance.append({
            'course': course,
            'total_classes': stats['total_classes'],
            'presents': stats['presents'],
            'absents': stats['absents'],
            'attendance_percentage': course_attendance_percentage
        })
    
    return jsonify({
        'success': True,
        'monthly_history': monthly_history,
        'course_wise_attendance': course_wise_attendance,
        'statistics': {
            'total_classes': total_classes,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': attendance_percentage
        },
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    })

@app.route('/api/student-recent-attendance', methods=['GET'])
def student_recent_attendance():
    student = request.args.get('student')
    limit = request.args.get('limit', 10)  # Default to 10 recent records
    
    if not student:
        return jsonify({'success': False, 'error': 'Missing student'}), 400
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    
    attendance_ref = db.collection('attendance').stream()
    all_history = []
    
    for doc in attendance_ref:
        data = doc.to_dict()
        records = data.get('records', {})
        if student in records:
            all_history.append({
                'course': data.get('course'),
                'date': data.get('date'),
                'status': records[student]
            })
    
    # Sort by date (most recent first) and take the most recent records
    all_history.sort(key=lambda x: x['date'], reverse=True)
    recent_history = all_history[:limit]
    
    return jsonify({
        'success': True,
        'recent_history': recent_history,
        'total_records': len(all_history)
    })

@app.route('/api/create-test-attendance', methods=['POST'])
def create_test_attendance():
    """Create sample attendance data for testing"""
    from datetime import datetime, timedelta
    import random
    
    # Get student email from request
    data = request.get_json()
    student_email = data.get('student_email')
    course = data.get('course', 'Operating System')
    
    if not student_email:
        return jsonify({'success': False, 'error': 'Student email required'}), 400
    
    # Create attendance records for the past month
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    last_month = first_day_of_month - timedelta(days=1)
    start_date = last_month.replace(day=1)
    
    created_records = 0
    
    # Create attendance for each weekday in the past month
    current_date = start_date
    while current_date <= today:
        # Skip weekends (Saturday = 5, Sunday = 6)
        if current_date.weekday() < 5:  # Monday to Friday
            date_str = current_date.strftime('%Y-%m-%d')
            doc_id = f'{course}_{date_str}'
            
            # Randomly mark as present (80% chance) or absent (20% chance)
            status = 'Present' if random.random() < 0.8 else 'Absent'
            
            # Check if record already exists
            existing_doc = db.collection('attendance').document(doc_id).get()
            if existing_doc.exists:
                # Update existing record
                existing_data = existing_doc.to_dict()
                existing_data['records'][student_email] = status
                db.collection('attendance').document(doc_id).set(existing_data)
            else:
                # Create new record
                db.collection('attendance').document(doc_id).set({
                    'course': course,
                    'date': date_str,
                    'marked_by': 'test_faculty@example.com',
                    'records': {student_email: status}
                })
            
            created_records += 1
        
        current_date += timedelta(days=1)
    
    return jsonify({
        'success': True, 
        'message': f'Created {created_records} attendance records for {student_email}',
        'course': course,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d')
        }
    })

@app.route('/api/attendance-report', methods=['GET'])
def attendance_report():
    course = request.args.get('course')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    if not course or not from_date or not to_date:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    attendance_ref = db.collection('attendance').stream()
    report = []
    for doc in attendance_ref:
        data = doc.to_dict()
        if data.get('course') == course and from_date <= data.get('date') <= to_date:
            report.append(data)
    return jsonify({'success': True, 'report': report})

@app.route('/api/download-attendance-report', methods=['GET'])
def download_attendance_report():
    course = request.args.get('course')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    if not course or not from_date or not to_date:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    attendance_ref = db.collection('attendance').stream()
    report = []
    for doc in attendance_ref:
        data = doc.to_dict()
        if data.get('course') == course and from_date <= data.get('date') <= to_date:
            report.append(data)
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont('Helvetica', 12)
    p.drawString(100, 800, f'Attendance Report for {course}')
    y = 780
    for entry in report:
        p.drawString(100, y, f"Date: {entry['date']} - Marked by: {entry.get('marked_by', '')}")
        y -= 20
        for student, status in entry['records'].items():
            p.drawString(120, y, f"{student}: {status}")
            y -= 15
        y -= 10
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='attendance_report.pdf', mimetype='application/pdf')

@app.route('/api/download-student-attendance', methods=['GET'])
def download_student_attendance():
    student = request.args.get('student')
    course = request.args.get('course')
    month = request.args.get('month')  # format: YYYY-MM
    if not student or not course or not month:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    attendance_ref = db.collection('attendance').stream()
    report = []
    for doc in attendance_ref:
        data = doc.to_dict()
        if (
            data.get('course') == course and
            data.get('date', '').startswith(month) and
            student in data.get('records', {})
        ):
            report.append({
                'date': data.get('date'),
                'status': data['records'][student]
            })
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont('Helvetica', 12)
    p.drawString(100, 800, f'Attendance Report for {student}')
    p.drawString(100, 780, f'Course: {course} | Month: {month}')
    y = 760
    for entry in sorted(report, key=lambda x: x['date']):
        p.drawString(100, y, f"Date: {entry['date']} - Status: {entry['status']}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='student_attendance_report.pdf', mimetype='application/pdf')

# --- Queries Endpoints ---
@app.route('/api/submit-query', methods=['POST'])
def submit_query():
    data = request.get_json()
    doc_ref = db.collection('queries').document()
    doc_ref.set(data)
    return jsonify({'success': True, 'message': 'Query submitted!'})

@app.route('/api/get-queries', methods=['GET'])
def get_queries():
    queries_ref = db.collection('queries').stream()
    queries = []
    for doc in queries_ref:
        q = doc.to_dict()
        q['id'] = doc.id
        queries.append(q)
    return jsonify({'success': True, 'queries': queries})

@app.route('/api/delete-query/<query_id>', methods=['DELETE'])
def delete_query(query_id):
    db.collection('queries').document(query_id).delete()
    return jsonify({'success': True, 'message': 'Query deleted.'})

@app.route('/api/update-query-status/<query_id>', methods=['PATCH'])
def update_query_status(query_id):
    data = request.get_json()
    status = data.get('status')
    db.collection('queries').document(query_id).update({'status': status})
    return jsonify({'success': True, 'message': 'Status updated.'})

@app.route('/api/download-admit-card', methods=['GET'])
def download_admit_card():
    email = request.args.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'Missing email'}), 400
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    user_data = user_doc.to_dict()
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont('Helvetica-Bold', 18)
    p.drawString(100, 800, 'Admit Card')
    p.setFont('Helvetica', 14)
    p.drawString(100, 770, f"Name: {user_data.get('name', '')}")
    p.drawString(100, 750, f"Email: {user_data.get('email', '')}")
    p.drawString(100, 730, f"Course: {', '.join(user_data.get('courses', []))}")
    p.drawString(100, 710, f"Exam: End Semester Examination April 2024")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='admit_card.pdf', mimetype='application/pdf')

@app.route('/api/list-attendance', methods=['GET'])
def list_attendance():
    attendance_ref = db.collection('attendance').stream()
    attendance_list = []
    for doc in attendance_ref:
        data = doc.to_dict()
        attendance_list.append({
            'doc_id': doc.id,
            'course': data.get('course'),
            'date': data.get('date'),
            'students': list(data.get('records', {}).keys())
        })
    return jsonify({'attendance': attendance_list})

@app.route('/api/notify-low-attendance', methods=['POST'])
def api_notify_low_attendance():
    try:
        notify_students_from_attendance()
        return jsonify({'success': True, 'message': 'Low attendance emails sent.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
