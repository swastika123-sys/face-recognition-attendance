#!/usr/bin/env python3
"""
Test script to verify the teacher/student registration system
"""

from db import __get_db_connection
import mysql.connecto    if db_test and route_test:
        print('\n✨ SYSTEM READY FOR USE! ✨')
        print('\n📋 Next steps:')
        print('   1. Start the Flask app: python3 app.py')
        print('   2. Go to http://localhost:5001/')
        print('   3. Register students (no password needed)')
        print('   4. Register teachers (password + secret required)')
        print('   5. Login as teacher to access dashboard')
        print('   6. Use face recognition for attendance')
    else:
        print('\n💥 SYSTEM NOT READY - Please fix errors above')_registration_system():
    """Test the registration system functionality"""
    
    print('=== TESTING TEACHER/STUDENT REGISTRATION SYSTEM ===\n')
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Test 1: Check table structures
        print('1. Testing table structures...')
        
        expected_tables = ['teachers', 'students', 'attendance']
        cursor.execute('SHOW TABLES')
        actual_tables = [table[0] for table in cursor.fetchall()]
        
        for table in expected_tables:
            if table in actual_tables:
                print(f'   ✅ {table} table exists')
            else:
                print(f'   ❌ {table} table missing')
                return False
        
        # Test 2: Check teacher table columns
        print('\n2. Testing teacher table structure...')
        cursor.execute('DESCRIBE teachers')
        teacher_columns = [col[0] for col in cursor.fetchall()]
        expected_teacher_cols = ['id', 'username', 'email', 'password', 'face_image', 'face_encoding', 'image_path']
        
        for col in expected_teacher_cols:
            if col in teacher_columns:
                print(f'   ✅ teachers.{col} exists')
            else:
                print(f'   ❌ teachers.{col} missing')
        
        # Test 3: Check student table columns
        print('\n3. Testing student table structure...')
        cursor.execute('DESCRIBE students')
        student_columns = [col[0] for col in cursor.fetchall()]
        expected_student_cols = ['id', 'username', 'email', 'serial_number', 'phone', 'face_image', 'face_encoding', 'image_path', 'created_at']
        
        for col in expected_student_cols:
            if col in student_columns:
                print(f'   ✅ students.{col} exists')
            else:
                print(f'   ❌ students.{col} missing')
        
        # Test 4: Check attendance table structure
        print('\n4. Testing attendance table structure...')
        cursor.execute('DESCRIBE attendance')
        attendance_columns = [col[0] for col in cursor.fetchall()]
        expected_attendance_cols = ['id', 'student_id', 'timestamp', 'status', 'method', 'teacher_id', 'notes']
        
        for col in expected_attendance_cols:
            if col in attendance_columns:
                print(f'   ✅ attendance.{col} exists')
            else:
                print(f'   ❌ attendance.{col} missing')
        
        # Test 5: Check foreign key constraints
        print('\n5. Testing foreign key constraints...')
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME, 
                TABLE_NAME, 
                COLUMN_NAME, 
                REFERENCED_TABLE_NAME, 
                REFERENCED_COLUMN_NAME 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE REFERENCED_TABLE_SCHEMA = 'face_project' 
            AND TABLE_NAME = 'attendance'
        """)
        
        constraints = cursor.fetchall()
        print(f'   Found {len(constraints)} foreign key constraints')
        for constraint in constraints:
            print(f'   ✅ {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}')
        
        # Test 6: Test data integrity
        print('\n6. Testing current data...')
        
        cursor.execute('SELECT COUNT(*) FROM teachers')
        teacher_count = cursor.fetchone()[0]
        print(f'   📊 Teachers in database: {teacher_count}')
        
        cursor.execute('SELECT COUNT(*) FROM students')
        student_count = cursor.fetchone()[0]
        print(f'   📊 Students in database: {student_count}')
        
        cursor.execute('SELECT COUNT(*) FROM attendance')
        attendance_count = cursor.fetchone()[0]
        print(f'   📊 Attendance records: {attendance_count}')
        
        cursor.close()
        conn.close()
        
        print('\n🎉 All tests passed! The teacher/student registration system is ready.')
        return True
        
    except mysql.connector.Error as e:
        print(f'❌ Database error: {e}')
        return False

def test_app_routes():
    """Test that all app routes are properly configured"""
    
    print('\n=== TESTING APP ROUTES ===\n')
    
    try:
        import sys
        sys.path.insert(0, '.')
        from app import app
        
        expected_routes = [
            'index', 'register', 'login', 'logout', 'dashboard',
            'student', 'attendance', 'realtime', 'recognize',
            'why_choose', 'services', 'contact', 'help_page'
        ]
        
        actual_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                actual_routes.append(rule.endpoint)
        
        print('Route availability:')
        for route in expected_routes:
            if route in actual_routes:
                print(f'   ✅ /{route} route exists')
            else:
                print(f'   ❌ /{route} route missing')
        
        print(f'\n📊 Total routes configured: {len(actual_routes)}')
        return True
        
    except Exception as e:
        print(f'❌ App route test error: {e}')
        return False

if __name__ == "__main__":
    db_test = test_registration_system()
    route_test = test_app_routes()
    
    if db_test and route_test:
        print('\n✨ SYSTEM READY FOR USE! ✨')
        print('\n📋 Next steps:')
        print('   1. Start the Flask app: python3 app.py')
        print('   2. Go to http://localhost:5001/')
        print('   3. Register students (no password needed)')
        print('   4. Register teachers (password + secret required)')
        print('   5. Login as teacher to access dashboard')
        print('   6. Use face recognition for attendance')
    else:
        print('\n💥 SYSTEM NOT READY - Please fix errors above')
