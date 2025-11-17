from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from flask_cors import CORS
from datetime import datetime
from deepface import DeepFace
import numpy as np
import os
import csv
import mysql.connector
from PIL import Image
import base64
from io import BytesIO
import cv2
from db import __get_db_connection

app = Flask(__name__)
app.secret_key = 'supersecretkey'
CORS(app)
KNOWN_FACES_FOLDER = 'known_faces'

# DeepFace configuration
FACE_MODEL = 'Facenet'  # Good balance of accuracy and speed
DETECTOR_BACKEND = 'opencv'  # Most reliable
DISTANCE_THRESHOLD = 15.0  # Adjusted for real-world face recognition conditions
# Force reload after removing fake images - CLEANED

# Global storage for face embeddings and names
known_face_embeddings = []
known_face_names = []

def extract_face_embedding(image_array):
    """Extract face embedding from image array using DeepFace"""
    try:
        # DeepFace expects RGB images
        result = DeepFace.represent(
            img_path=image_array,
            model_name=FACE_MODEL,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False  # More lenient for edge cases
        )
        
        if result and len(result) > 0:
            embedding = np.array(result[0]['embedding'])
            print(f"DEBUG: Successfully extracted {len(embedding)}-dim embedding using represent")
            return embedding
        else:
            print("DEBUG: DeepFace.represent returned empty result - no face detected")
            return None
            
    except Exception as e:
        print(f"DEBUG: Face embedding extraction failed with DeepFace.represent: {e}")
        return None

def compare_faces(known_embeddings, face_embedding, threshold=DISTANCE_THRESHOLD):
    """Compare face embedding against known faces"""
    if not known_embeddings or face_embedding is None:
        return [], []
    
    distances = []
    for known_embedding in known_embeddings:
        # Calculate cosine distance (same as DeepFace uses internally)
        distance = np.linalg.norm(known_embedding - face_embedding)
        distances.append(distance)
    
    return distances, [i for i, d in enumerate(distances) if d < threshold]

def load_known_faces(folder=KNOWN_FACES_FOLDER):
    """Load known faces from students table only"""
    global known_face_embeddings, known_face_names
    
    known_face_embeddings = []
    known_face_names = []
    
    # Load from students table only
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT serial_number, username, face_encoding FROM students WHERE face_encoding IS NOT NULL")
        student_faces = cursor.fetchall()
        
        for serial_number, username, face_encoding_str in student_faces:
            if face_encoding_str:
                try:
                    # Convert string back to numpy array
                    face_encoding = np.array(eval(face_encoding_str))
                    known_face_embeddings.append(face_encoding)
                    known_face_names.append(f"{serial_number}_{username}")  # Use serial_username format
                    print(f"DEBUG: Loaded face embedding from database for: {serial_number}_{username}")
                except Exception as e:
                    print(f"DEBUG: Error parsing face encoding for {username}: {e}")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"DEBUG: Database error loading faces: {e}")
    
    print(f"DEBUG: Total face embeddings loaded from database: {len(known_face_embeddings)} - Names: {known_face_names}")
    
    # Keep filesystem images for debugging - don't delete them
    if os.path.exists(folder):
        try:
            files_in_folder = os.listdir(folder)
            print(f"DEBUG: Filesystem has {len([f for f in files_in_folder if f.lower().endswith(('.jpg', '.png'))])} face images for debugging/testing")
        except Exception as e:
            print(f"DEBUG: Error checking filesystem images: {e}")

def init_db():
    """Initialize database with student and teacher registration system"""
    conn = None
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Create teachers table
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
        
        # Create students table (can self-register)
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
        
        # Create attendance table with manual edit capabilities
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
        
        conn.commit()
        print("MySQL database initialized successfully! (Tables verified/created as needed)")
    except mysql.connector.Error as e:
        print("DB Init error:", e)
    finally:
        if conn is not None and conn.is_connected():
            cursor.close()
            conn.close()

init_db()
load_known_faces()

def mark_attendance(name):
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    
    # Save to CSV file (backup)
    with open('attendance.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date_str, time_str, name])
    
    # Save to MySQL database
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Extract serial number from name (format: "01_StudentName")
        if '_' in name:
            serial_number = name.split('_')[0]
        else:
            serial_number = name  # Fallback for old format
        
        # Find student by serial number
        cursor.execute("SELECT id FROM students WHERE serial_number = %s", (serial_number,))
        student_row = cursor.fetchone()
        
        if student_row:
            student_id = student_row[0]
            teacher_id = session.get('user_id') if session.get('user_type') == 'teacher' else None
            
            # Insert attendance record
            cursor.execute("""
                INSERT INTO attendance (student_id, timestamp, status, method, teacher_id) 
                VALUES (%s, %s, 'Present', 'Face Recognition', %s)
            """, (student_id, now, teacher_id))
            
            conn.commit()
            print(f"Attendance marked in database for {name} (Student ID: {student_id})")
        else:
            print(f"Student with serial number {serial_number} not found in database")
        
    except mysql.connector.Error as e:
        print(f"Database attendance error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Student-specific fields
        serial_number = request.form.get('serial_number')
        phone = request.form.get('phone')
        
        # Teacher-specific fields
        teacher_secret = request.form.get('teacher_secret')
        
        # Face image data
        face_image = request.form.get('face_image')
        
        if user_type == 'teacher':
            # Teacher registration validation
            if not all([username, email, password, teacher_secret]):
                flash("Username, email, password, and teacher secret are required for teacher registration", "danger")
                return render_template('register.html')
            
            # Verify teacher secret
            if teacher_secret.lower() != 'admin':
                flash("Invalid teacher secret. Access denied.", "danger")
                return render_template('register.html')
            
            try:
                conn = __get_db_connection()
                cursor = conn.cursor()
                
                # Teachers don't need face images - just basic registration
                cursor.execute('''
                    INSERT INTO teachers (username, email, password)
                    VALUES (%s, %s, %s)
                ''', (username, email, password))
                
                conn.commit()
                flash("Teacher registration successful! You can now login.", "success")
                return redirect(url_for('login'))
                
            except mysql.connector.IntegrityError:
                flash("Username or email already exists", "danger")
                return render_template('register.html')
            except mysql.connector.Error as e:
                flash(f"Database error occurred: {e}", "danger")
                return render_template('register.html')
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
                    
        elif user_type == 'student':
            # Student registration validation
            if not all([username, email, serial_number, phone]):
                flash("Username, email, serial number, and phone are required for student registration", "danger")
                return render_template('register.html')
            
            if len(serial_number) < 1 or len(serial_number) > 10 or not serial_number.isalnum():
                flash("Serial number must be 1-10 characters (letters and numbers only)", "danger")
                return render_template('register.html')
            
            if len(phone) != 10 or not phone.isdigit():
                flash("Phone number must be exactly 10 digits", "danger")
                return render_template('register.html')
            
            try:
                conn = __get_db_connection()
                cursor = conn.cursor()
                
                # Save face image if provided
                face_encoding_str = None
                image_path = None
                
                if face_image:
                    try:
                        # Decode base64 image
                        img_data = base64.b64decode(face_image.split(',')[1])
                        img = Image.open(BytesIO(img_data)).convert('RGB')
                        
                        # Save to known_faces folder
                        if not os.path.exists(KNOWN_FACES_FOLDER):
                            os.makedirs(KNOWN_FACES_FOLDER)
                        
                        filename = f"{serial_number}_{username.replace(' ', '_')}.png"
                        image_path = os.path.join(KNOWN_FACES_FOLDER, filename)
                        img.save(image_path, format='PNG')
                        
                        # Extract face embedding
                        img_array = np.array(img, dtype=np.uint8)
                        face_embedding = extract_face_embedding(img_array)
                        if face_embedding is not None:
                            face_encoding_str = str(face_embedding.tolist())
                    except Exception as e:
                        print(f"Error processing face image: {e}")
                
                # Check for duplicate faces before inserting
                if face_encoding_str:
                    # Load current known faces from database only (not filesystem)
                    temp_embeddings, temp_names = load_faces_for_duplicate_check()
                    
                    # Convert the new face encoding back to numpy array
                    try:
                        new_face_embedding = np.array(eval(face_encoding_str))
                        
                        print(f"DEBUG: Checking for duplicate faces. Known faces: {len(temp_embeddings)}")
                        print(f"DEBUG: Known face names: {temp_names}")
                        
                        # Check against existing faces from database only
                        if len(temp_embeddings) > 0:
                            # Use a stricter threshold for duplicate detection (lower = more similar)
                            DUPLICATE_THRESHOLD = 3.0  # Much stricter than attendance threshold
                            distances, matches = compare_faces(temp_embeddings, new_face_embedding, DUPLICATE_THRESHOLD)
                            
                            print(f"DEBUG: Face distances: {[f'{name}: {dist:.3f}' for name, dist in zip(temp_names, distances)]}")
                            print(f"DEBUG: Duplicate threshold: {DUPLICATE_THRESHOLD}")
                            print(f"DEBUG: Matches found: {len(matches)}")
                            
                            if matches:
                                # Found a match - this person is already registered
                                best_match_idx = min(matches, key=lambda i: distances[i])
                                existing_name = temp_names[best_match_idx]
                                distance = distances[best_match_idx]
                                
                                print(f"DEBUG: Duplicate detected! {existing_name} with distance {distance:.3f}")
                                flash(f"Face already registered! Our AI detected you match an existing student: {existing_name} (similarity: {distance:.2f}). Please contact administrator if this is an error.", "danger")
                                return render_template('register.html')
                                
                    except Exception as e:
                        print(f"Error checking for duplicate faces: {e}")
                        # Continue with registration if face comparison fails
                
                cursor.execute('''
                    INSERT INTO students (username, email, serial_number, phone, face_image, face_encoding, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (username, email, serial_number, phone, face_image, face_encoding_str, image_path))
                
                conn.commit()
                
                # Reload known faces to include new student
                load_known_faces()
                
                # Provide appropriate success message based on whether face was captured
                if face_encoding_str:
                    flash("Student registration successful! Your face has been registered for attendance. You can now use the face recognition system.", "success")
                else:
                    flash("Student registration successful! Note: No face image was captured. You'll need to register your face later to use the face recognition system.", "warning")
                
                return render_template('register.html')
                
            except mysql.connector.IntegrityError:
                flash("Username, email, or serial number already exists", "danger")
                return render_template('register.html')
            except mysql.connector.Error as e:
                flash(f"Database error occurred: {e}", "danger")
                return render_template('register.html')
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            flash("Please select a valid user type", "danger")
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash("Username and password required", "danger")
            return render_template('login.html')

        try:
            conn = __get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM teachers WHERE username = %s", (username,))
            row = cursor.fetchone()
        except mysql.connector.Error as e:
            flash("Database connection error", "danger")
            return render_template('login.html')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

        if row and row[1] == password:
            session['user'] = username
            session['user_type'] = 'teacher'
            session['user_id'] = row[0]
            flash("Teacher login successful!", "success")
            return redirect(url_for('dashboard'))
        
        flash("Invalid teacher credentials.", "danger")
        return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/student')
def student():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    # Get all students from database
    students_list = []
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, serial_number, username, email, phone, face_encoding, created_at FROM students ORDER BY serial_number")
        students_list = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('student.html', students=students_list)

@app.route('/add_student', methods=['POST'])
def add_student():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    serial_number = request.form.get('serial_number')
    username = request.form.get('username')
    email = request.form.get('email')
    phone = request.form.get('phone')
    photo = request.files.get('photo')
    
    # Validation
    if not all([serial_number, username, email, phone, photo]):
        flash("All fields including photo are required", "danger")
        return redirect(url_for('student'))
    
    if len(serial_number) < 1 or len(serial_number) > 10 or not serial_number.isalnum():
        flash("Serial number must be 1-10 characters (letters and numbers only)", "danger")
        return redirect(url_for('student'))
    
    if len(phone) != 10 or not phone.isdigit():
        flash("Phone number must be exactly 10 digits", "danger")
        return redirect(url_for('student'))
    
    try:
        # Save photo to known_faces folder
        if not os.path.exists(KNOWN_FACES_FOLDER):
            os.makedirs(KNOWN_FACES_FOLDER)
        
        filename = f"{serial_number}_{username.replace(' ', '_')}.png"
        filepath = os.path.join(KNOWN_FACES_FOLDER, filename)
        
        # Convert and save as PNG
        img = Image.open(photo).convert('RGB')
        img.save(filepath, format='PNG')
        
        # Extract face embedding
        img_array = np.array(img, dtype=np.uint8)
        face_embedding = extract_face_embedding(img_array)
        
        # Insert into database
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO students (serial_number, username, email, phone, image_path, face_encoding)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (serial_number, username, email, phone, filepath, 
              str(face_embedding.tolist()) if face_embedding is not None else None))
        
        conn.commit()
        
        # Reload known faces
        load_known_faces()
        
        flash(f"Student {username} (#{serial_number}) added successfully!", "success")
        
    except mysql.connector.IntegrityError:
        flash("Serial number or username already exists", "danger")
    except Exception as e:
        flash(f"Error adding student: {e}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('student'))

@app.route('/attendance')
def attendance():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    # Read attendance data from database
    attendance_data = []
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Query attendance records with student information
        cursor.execute("""
            SELECT a.id, DATE(a.timestamp) as date, TIME(a.timestamp) as time, 
                   s.username, s.serial_number, a.status, a.method, a.notes
            FROM attendance a 
            JOIN students s ON a.student_id = s.id 
            ORDER BY a.timestamp DESC
        """)
        
        rows = cursor.fetchall()
        for row in rows:
            attendance_data.append({
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'name': row[3],
                'serial_number': row[4],
                'status': row[5],
                'method': row[6],
                'notes': row[7]
            })
            
    except mysql.connector.Error as e:
        print(f"Database error reading attendance: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('attendance.html', attendance_data=attendance_data)

@app.route('/realtime')
def realtime():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('realtime.html')

@app.route('/test_response')
def test_response():
    """Test endpoint to verify server responses"""
    return jsonify(recognized=["TEST: Server is working correctly"])

@app.route('/recognize', methods=['POST'])
def recognize():
    if not session.get('user'):
        return jsonify({"error": "Not logged in", "success": False}), 401
        
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "No image data", "success": False}), 400

    img_data = data['image']
    try:
        bts = base64.b64decode(img_data.split(',')[1])
        img = Image.open(BytesIO(bts)).convert('RGB')
    except Exception as e:
        return jsonify({"error": f"Invalid image data: {e}", "success": False}), 400

    img.thumbnail((800, 800))
    arr = np.ascontiguousarray(np.array(img, dtype=np.uint8))
    
    print(f"DEBUG: Incoming image array shape: {arr.shape}, dtype: {arr.dtype}")
    
    # Make sure it's RGB (3 channels)
    if len(arr.shape) != 3 or arr.shape[2] != 3:
        return jsonify({"error": "Image must be RGB", "success": False}), 400
    
    # Use the SAME detection and embedding extraction method for consistency
    print("DEBUG: Extracting face embedding with DeepFace (single method)...")
    face_embedding = extract_face_embedding(arr)
    
    if face_embedding is None:
        print("DEBUG: No face detected in the image")
        return jsonify({"error": "⚠️ No face detected. Please position yourself in front of the camera", "success": False}), 400
    
    # Check for multiple faces using the same method that successfully detected a face
    try:
        # Use represent to check for multiple faces since it already worked for extraction
        all_representations = DeepFace.represent(
            img_path=arr,
            model_name=FACE_MODEL,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False  # Same as extract_face_embedding
        )
        
        num_faces = len(all_representations) if all_representations else 0
        print(f"DEBUG: Number of faces detected by represent: {num_faces}")
        
        if num_faces > 1:
            print("DEBUG: Multiple faces detected - attendance registration blocked")
            return jsonify({
                "error": f"Multiple faces detected ({num_faces}). Please ensure only one person is in the frame.",
                "success": False,
                "multiple_faces": True
            }), 400
            
    except Exception as e:
        print(f"DEBUG: Multiple face check error: {e}")
        # If multiple face check fails but we have an embedding, continue (assume single face)
    
    print(f"DEBUG: Known face embeddings: {len(known_face_embeddings)} ({known_face_names})")
    
    if len(known_face_embeddings) == 0:
        print("DEBUG: No known faces in database to compare against")
        return jsonify({
            "success": False,
            "recognized": False,
            "message": "No registered students found in database"
        })
    
    # Compare with known faces
    distances, matches = compare_faces(known_face_embeddings, face_embedding, DISTANCE_THRESHOLD)
    
    print(f"DEBUG: Distances to all known faces: {[f'{name}: {dist:.3f}' for name, dist in zip(known_face_names, distances)]}")
    print(f"DEBUG: Recognition threshold: {DISTANCE_THRESHOLD}")
    print(f"DEBUG: Matches found: {len(matches)}")
    
    if matches:
        # Get the best match (smallest distance)
        best_match_idx = min(matches, key=lambda i: distances[i])
        recognized_name = known_face_names[best_match_idx]
        distance = distances[best_match_idx]
        
        print(f"DEBUG: Face recognized as {recognized_name} (distance: {distance:.3f})")
        mark_attendance(recognized_name)
        
        # Get student details for display
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='face_project'
            )
            cursor = conn.cursor()
            cursor.execute("SELECT serial_number, username FROM students WHERE username = %s", (recognized_name,))
            student_data = cursor.fetchone()
            
            if student_data:
                serial_number, username = student_data
                # Format message for display
                message = f"Welcome {username}! Attendance marked successfully."
                return jsonify({
                    "success": True,
                    "recognized": True,  # Boolean for dashboard compatibility
                    "message": message,  # String for dashboard
                    "student": {
                        "serial_number": serial_number,
                        "name": username
                    }
                })
            else:
                # Format message for display
                message = f"Welcome {recognized_name}! Attendance marked successfully."
                return jsonify({
                    "success": True,
                    "recognized": True,  # Boolean for dashboard compatibility
                    "message": message,  # String for dashboard
                    "student": {
                        "serial_number": "Unknown",
                        "name": recognized_name
                    }
                })
        except Exception as e:
            print(f"Error fetching student details: {e}")
            # Format message for display
            message = f"Welcome {recognized_name}! Attendance marked successfully."
            return jsonify({
                "success": True,
                "recognized": True,  # Boolean for dashboard compatibility
                "message": message,  # String for dashboard
                "student": {
                    "serial_number": "Unknown",
                    "name": recognized_name
                }
            })
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    else:
        print(f"DEBUG: Face not recognized - all distances >= {DISTANCE_THRESHOLD}")
        min_distance = min(distances) if distances else float('inf')
        closest_name = known_face_names[distances.index(min_distance)] if distances else "None"
        print(f"DEBUG: Closest match was {closest_name} at distance {min_distance:.3f}")
        return jsonify({
            "success": False,
            "recognized": False,
            "message": "Face not recognized. Please try again."
        })

@app.route('/why_choose')
def why_choose():
    return render_template('why_choose.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/setting', methods=['GET', 'POST'])
def setting():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        teacher_email = request.form.get('teacherEmail')
        user_id = session.get('user_id')
        
        if teacher_email:
            try:
                conn = __get_db_connection()
                cursor = conn.cursor()
                # Update teacher email only
                cursor.execute(
                    "UPDATE teachers SET email = %s WHERE id = %s",
                    (teacher_email, user_id)
                )
                conn.commit()
                flash("Settings updated successfully!", "success")
            except mysql.connector.Error as e:
                flash(f"Failed to update settings: {e}", "danger")
            finally:
                if conn and conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            flash("Email is required!", "danger")
            
        return redirect(url_for('setting'))
    
    # GET request - show current settings
    teacher_data = {}
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM teachers WHERE id = %s", (session.get('user_id'),))
        row = cursor.fetchone()
        if row:
            teacher_data = {'email': row[0] or ''}
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('setting.html', teacher_data=teacher_data)

@app.route('/automated')
def automated():
    return render_template('automated.html')

@app.route('/CONTACT')
def contact():
    return render_template('CONTACT.HTML')

# Manual attendance management routes
@app.route('/manual_attendance', methods=['POST'])
def manual_attendance():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    student_serial = request.form.get('student_serial')
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Find student by serial number
        cursor.execute("SELECT id FROM students WHERE serial_number = %s", (student_serial,))
        student_row = cursor.fetchone()
        
        if student_row:
            student_id = student_row[0]
            teacher_id = session.get('user_id')
            
            # Insert manual attendance record
            cursor.execute("""
                INSERT INTO attendance (student_id, status, method, teacher_id, notes) 
                VALUES (%s, %s, 'Manual', %s, %s)
            """, (student_id, status, teacher_id, notes))
            
            conn.commit()
            flash(f"Manual attendance recorded for student #{student_serial}", "attendance_success")
        else:
            flash(f"Student with serial number {student_serial} not found", "attendance_danger")
            
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('attendance'))

@app.route('/edit_attendance/<int:attendance_id>', methods=['POST'])
def edit_attendance(attendance_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Update attendance record
        cursor.execute("""
            UPDATE attendance 
            SET status = %s, notes = %s, teacher_id = %s
            WHERE id = %s
        """, (status, notes, session.get('user_id'), attendance_id))
        
        conn.commit()
        flash("Attendance record updated successfully", "attendance_success")
        
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "attendance_danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('attendance'))

@app.route('/delete_attendance/<int:attendance_id>', methods=['POST'])
def delete_attendance(attendance_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Delete attendance record
        cursor.execute("DELETE FROM attendance WHERE id = %s", (attendance_id,))
        conn.commit()
        flash("Attendance record deleted successfully", "attendance_success")
        
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "attendance_danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('attendance'))

def load_faces_for_duplicate_check():
    """Load known faces from database only for duplicate checking during registration"""
    temp_embeddings = []
    temp_names = []
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT serial_number, username, face_encoding FROM students WHERE face_encoding IS NOT NULL")
        student_faces = cursor.fetchall()
        
        for serial_number, username, face_encoding_str in student_faces:
            if face_encoding_str:
                try:
                    # Convert string back to numpy array
                    face_encoding = np.array(eval(face_encoding_str))
                    temp_embeddings.append(face_encoding)
                    temp_names.append(f"{serial_number}_{username}")
                    print(f"DEBUG: Loaded face for duplicate check: {serial_number}_{username}")
                except Exception as e:
                    print(f"DEBUG: Error parsing face encoding for duplicate check {username}: {e}")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"DEBUG: Database error loading faces for duplicate check: {e}")
    
    print(f"DEBUG: Loaded {len(temp_embeddings)} faces from database for duplicate checking")
    return temp_embeddings, temp_names

@app.route('/detect_face', methods=['POST'])
def detect_face():
    """Real-time face detection for live camera feed - works for all users"""
    
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "No image data", "faces": []}), 400

    img_data = data['image']
    try:
        bts = base64.b64decode(img_data.split(',')[1])
        img = Image.open(BytesIO(bts)).convert('RGB')
    except Exception as e:
        return jsonify({"error": f"Invalid image data: {e}", "faces": []}), 400

    img.thumbnail((400, 300))  # Match canvas size
    arr = np.ascontiguousarray(np.array(img, dtype=np.uint8))
    
    # Make sure it's RGB (3 channels)
    if len(arr.shape) != 3 or arr.shape[2] != 3:
        return jsonify({"error": "Image must be RGB", "faces": []}), 400
    
    try:
        # Use the SAME face detection method as /recognize endpoint for consistency
        face_objs = DeepFace.extract_faces(
            img_path=arr,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False,  # Same as /recognize endpoint
            align=True
        )
        
        faces_detected = []
        
        # Process each detected face using the same logic as /recognize
        for i, face_obj in enumerate(face_objs):
            # To get coordinates, we need to use analyze since extract_faces doesn't return coordinates
            try:
                face_analysis = DeepFace.analyze(
                    img_path=arr,
                    actions=['emotion'],
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=False  # Same as extract_faces
                )
                
                if not isinstance(face_analysis, list):
                    face_analysis = [face_analysis]
                
                if i < len(face_analysis):
                    region = face_analysis[i].get('region', {})
                    x = region.get('x', 0)
                    y = region.get('y', 0)
                    w = region.get('w', 100)
                    h = region.get('h', 100)
                else:
                    # Fallback coordinates
                    x, y, w, h = 50, 50, 100, 100
            except:
                # Fallback coordinates if analyze fails
                x, y, w, h = 50, 50, 100, 100
            
            # Try to identify the face if logged in - SAME LOGIC AS /recognize
            face_name = "UNREGISTERED"
            display_name = "UNREGISTERED"
            status = "unregistered"
            
            if session.get('user') and len(known_face_embeddings) > 0:
                # Use the SAME embedding extraction method as /recognize endpoint
                face_embedding = extract_face_embedding(arr)
                if face_embedding is not None:
                    distances, matches = compare_faces(known_face_embeddings, face_embedding, DISTANCE_THRESHOLD)
                    
                    if matches:
                        # Found a match
                        best_match_idx = min(matches, key=lambda i: distances[i])
                        face_name = known_face_names[best_match_idx]  # Format: "12_swas1"
                        status = "registered"
                        
                        # Format display name as "Serial: Name"
                        if '_' in face_name:
                            serial, name = face_name.split('_', 1)
                            display_name = f"#{serial}: {name}"
                        else:
                            display_name = face_name
            
            faces_detected.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "name": face_name,
                "display_name": display_name,
                "status": status
            })
        
        return jsonify({
            "success": True,
            "faces": faces_detected,
            "total_faces": len(faces_detected)
        })
        
    except Exception as e:
        print(f"Face detection error: {e}")
        # Check if it's a "No face detected" error from DeepFace
        if "Face could not be detected" in str(e) or "no face" in str(e).lower():
            print("DEBUG: No face detected by DeepFace - returning empty result")
            return jsonify({
                "success": True,
                "faces": [],
                "total_faces": 0
            })
        else:
            print(f"DEBUG: Unexpected face detection error: {e}")
            return jsonify({
                "success": True,
                "faces": [],
                "total_faces": 0
            })

# Student management routes - View, Edit, Delete
@app.route('/view_student/<int:student_id>')
def view_student(student_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, serial_number, username, email, phone, image_path, 
                   face_encoding, created_at 
            FROM students WHERE id = %s
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            flash("Student not found", "danger")
            return redirect(url_for('student'))
            
        # Get attendance history
        cursor.execute("""
            SELECT DATE(timestamp) as date, TIME(timestamp) as time, 
                   status, method, notes
            FROM attendance WHERE student_id = %s 
            ORDER BY timestamp DESC LIMIT 10
        """, (student_id,))
        attendance_history = cursor.fetchall()
        
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('student'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('view_student.html', student=student, attendance_history=attendance_history)

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        try:
            conn = __get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE students 
                SET username = %s, phone = %s, email = %s
                WHERE id = %s
            """, (username, phone, email, student_id))
            conn.commit()
            flash("Student updated successfully!", "success")
            return redirect(url_for('student'))
            
        except mysql.connector.Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    # GET request - show edit form
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, serial_number, username, email, phone
            FROM students WHERE id = %s
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            flash("Student not found", "danger")
            return redirect(url_for('student'))
            
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('student'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        
        # Get student info before deletion for cleanup
        cursor.execute("SELECT serial_number, username, image_path FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if student:
            serial_number, username, image_path = student
            
            # Delete from database (attendance records will be deleted by CASCADE)
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            conn.commit()
            
            # Remove image file if exists
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"Error removing image file: {e}")
            
            # Reload known faces to remove deleted student
            load_known_faces()
            
            flash(f"Student {username} (#{serial_number}) deleted successfully!", "success")
        else:
            flash("Student not found", "danger")
            
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('student'))

# Route to serve images from known_faces folder
@app.route('/known_faces/<filename>')
def serve_image(filename):
    """Serve images from the known_faces folder to the frontend"""
    return send_from_directory(KNOWN_FACES_FOLDER, filename)

if __name__ == '__main__':
    # Auto-reload enabled for development convenience
    print("🚀 Starting Flask application...")
    print("📍 Access the app at: http://localhost:5001")
    print("🔄 Auto-reload is ENABLED - app will restart when files change")
    app.run(debug=True, port=5001, use_reloader=True)
