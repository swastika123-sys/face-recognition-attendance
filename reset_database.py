#!/usr/bin/env python3
"""
Database reset script to recreate tables with the new structure
"""

from db import __get_db_connection
import mysql.connector

def reset_database():
    """Drop all tables and recreate with new structure"""
    
    print('=== RESETTING DATABASE STRUCTURE ===\n')
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Drop existing tables
        print('1. Dropping existing tables...')
        cursor.execute('DROP TABLE IF EXISTS attendance')
        print('   ✅ Dropped attendance table')
        
        cursor.execute('DROP TABLE IF EXISTS students')
        print('   ✅ Dropped students table')
        
        cursor.execute('DROP TABLE IF EXISTS admins')
        print('   ✅ Dropped admins table')
        
        # Create admins table
        print('\n2. Creating new table structure...')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
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
        print('   ✅ Created admins table')
        
        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                serial_number VARCHAR(2) NOT NULL UNIQUE,
                phone VARCHAR(10) NOT NULL,
                face_image LONGTEXT,
                face_encoding TEXT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('   ✅ Created students table')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('Present', 'Absent', 'Late') DEFAULT 'Present',
                method ENUM('Face Recognition', 'Manual') DEFAULT 'Face Recognition',
                admin_id INT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL
            )
        ''')
        print('   ✅ Created attendance table')
        
        conn.commit()
        print('\n🎉 Database reset completed successfully!')
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f'❌ Database error: {e}')
        return False

if __name__ == "__main__":
    if reset_database():
        print('\n✨ Ready to restart your Flask application! ✨')
    else:
        print('\n💥 Database reset failed!')
