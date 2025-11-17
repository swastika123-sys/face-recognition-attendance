#!/usr/bin/env python3
"""
Database setup script for Face Recognition System
Creates separate tables for admins and students
"""

from db import __get_db_connection
import mysql.connector

def setup_database():
    """Create all necessary tables for the face recognition system"""
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        print('=== CREATING DATABASE TABLES ===')
        
        # Create admins table (renamed to teachers for consistency)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                face_image LONGTEXT,
                face_encoding TEXT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('✅ Created teachers table')
        
        # Create students table (no password required)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                serial_number VARCHAR(10) NOT NULL UNIQUE,
                phone VARCHAR(10) NOT NULL,
                face_image LONGTEXT,
                face_encoding TEXT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('✅ Created students table')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('Present', 'Absent', 'Late') DEFAULT 'Present',
                method ENUM('Face Recognition', 'Manual') DEFAULT 'Face Recognition',
                teacher_id INT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
            )
        ''')
        print('✅ Created attendance table')
        
        # Create teacher_sessions table for login tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP NULL,
                ip_address VARCHAR(45),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            )
        ''')
        print('✅ Created teacher_sessions table')
        
        conn.commit()
        print('\n✅ All tables created successfully!')
        
        # Show table structure
        print('\n=== TABLE STRUCTURES ===')
        tables = ['teachers', 'students', 'attendance', 'teacher_sessions']
        
        for table in tables:
            print(f'\n--- {table.upper()} TABLE ---')
            cursor.execute(f'DESCRIBE {table}')
            columns = cursor.fetchall()
            for col in columns:
                print(f'  {col[0]} ({col[1]}) - Null: {col[2]}, Key: {col[3]}')
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f'❌ Database error: {e}')
        return False

if __name__ == "__main__":
    success = setup_database()
    if success:
        print('\n🎉 Database setup completed successfully!')
    else:
        print('\n💥 Database setup failed!')
