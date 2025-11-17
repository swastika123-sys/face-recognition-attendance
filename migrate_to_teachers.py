#!/usr/bin/env python3
"""
Migration script to rename 'admins' table to 'teachers' and update references
"""

from db import __get_db_connection
import mysql.connector

def migrate_admin_to_teacher():
    """Migrate admins table to teachers table"""
    
    print('=== MIGRATING ADMIN TABLE TO TEACHERS ===\n')
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Step 1: Check if admins table exists
        cursor.execute("SHOW TABLES LIKE 'admins'")
        admin_exists = cursor.fetchone()
        
        cursor.execute("SHOW TABLES LIKE 'teachers'")
        teacher_exists = cursor.fetchone()
        
        if not admin_exists and teacher_exists:
            print('✅ Migration already completed - teachers table exists')
            return True
            
        if not admin_exists:
            print('❌ No admins table found to migrate')
            return False
            
        print('1. Found admins table - starting migration...')
        
        # Step 2: Create teachers table with same structure
        print('2. Creating teachers table...')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                face_image LONGTEXT,
                face_encoding TEXT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Step 3: Copy data from admins to teachers
        print('3. Copying data from admins to teachers...')
        cursor.execute('INSERT INTO teachers SELECT * FROM admins')
        
        # Step 4: Update attendance table foreign key
        print('4. Updating attendance table...')
        
        # First, add teacher_id column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE attendance ADD COLUMN teacher_id INT')
        except mysql.connector.Error:
            pass  # Column might already exist
        
        # Copy admin_id values to teacher_id
        cursor.execute('UPDATE attendance SET teacher_id = admin_id WHERE admin_id IS NOT NULL')
        
        # Drop old foreign key constraint and column
        try:
            cursor.execute('ALTER TABLE attendance DROP FOREIGN KEY attendance_ibfk_2')
        except mysql.connector.Error:
            pass
        
        try:
            cursor.execute('ALTER TABLE attendance DROP COLUMN admin_id')
        except mysql.connector.Error:
            pass
        
        # Add new foreign key constraint
        cursor.execute('''
            ALTER TABLE attendance 
            ADD CONSTRAINT fk_teacher_id 
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        ''')
        
        # Step 5: Drop admins table
        print('5. Dropping old admins table...')
        cursor.execute('DROP TABLE admins')
        
        conn.commit()
        print('\n✅ Migration completed successfully!')
        print('   - admins table renamed to teachers')
        print('   - attendance.admin_id renamed to attendance.teacher_id')
        print('   - All data preserved')
        
        return True
        
    except mysql.connector.Error as e:
        print(f'❌ Migration error: {e}')
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    success = migrate_admin_to_teacher()
    if success:
        print('\n🎉 Ready to use the updated teacher system!')
    else:
        print('\n💥 Migration failed - please check errors above')
