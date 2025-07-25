def calculate_attendance_percentage(student_id, course_id, db_connection):
    """
    Calculates and updates the attendance percentage of a student for a specific course.
    """
    cursor = db_connection.cursor()

    # 1. Get total and attended classes for the student in the course
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_classes,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS attended_classes
        FROM attendance
        WHERE student_id = %s AND course_id = %s
    """, (student_id, course_id))

    result = cursor.fetchone()
    total_classes = result[0]
    attended_classes = result[1] or 0

    # 2. Calculate percentage
    if total_classes == 0:
        attendance_percentage = 0.0
    else:
        attendance_percentage = (attended_classes / total_classes) * 100

    # 3. Update or store the result in a separate progress tracking table (optional)
    cursor.execute("""
        INSERT INTO student_progress (student_id, course_id, attendance_percentage)
        VALUES (%s, %s, %s)
        ON CONFLICT (student_id, course_id) DO UPDATE
        SET attendance_percentage = EXCLUDED.attendance_percentage
    """, (student_id, course_id, attendance_percentage))

    db_connection.commit()
    cursor.close()

    return attendance_percentage
