#!/usr/bin/env python3
"""
Test script to verify that /detect_face and /recognize endpoints are consistent
This verifies the fix for the "face detected but not recognized" issue
"""

import requests
import base64
import json
import os
from PIL import Image
import io

def load_test_image(image_path):
    """Load an image and convert to base64 for API testing"""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    
    # Convert to base64 with data URL prefix
    b64_data = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/png;base64,{b64_data}"

def test_endpoint_consistency():
    """Test that both endpoints detect faces consistently"""
    base_url = "http://localhost:5001"
    
    # First, login as a teacher to test both endpoints
    print("🔐 Logging in as teacher...")
    login_data = {
        'username': 'admin',  # Assuming there's an admin teacher
        'password': 'admin'
    }
    
    session = requests.Session()
    login_response = session.post(f"{base_url}/login", data=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed. Creating test teacher...")
        # Try to register a teacher first
        register_data = {
            'user_type': 'teacher',
            'username': 'testteacher',
            'email': 'test@teacher.com',
            'password': 'testpass',
            'teacher_secret': 'admin'
        }
        register_response = session.post(f"{base_url}/register", data=register_data)
        
        # Now try login again
        login_data = {
            'username': 'testteacher',
            'password': 'testpass'
        }
        login_response = session.post(f"{base_url}/login", data=login_data)
    
    if "login" in login_response.url:
        print("❌ Still couldn't login. Testing without authentication...")
        use_auth = False
    else:
        print("✅ Login successful!")
        use_auth = True
    
    # Test with existing face images
    test_images = []
    known_faces_dir = "/Users/swastika/Desktop/projectface.html/known_faces"
    
    if os.path.exists(known_faces_dir):
        for filename in os.listdir(known_faces_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(known_faces_dir, filename)
                test_images.append((filename, image_path))
    
    if not test_images:
        print("⚠️ No test images found in known_faces directory")
        return
    
    print(f"\n🧪 Testing {len(test_images)} images for endpoint consistency...")
    
    for filename, image_path in test_images[:2]:  # Test first 2 images
        print(f"\n📸 Testing image: {filename}")
        
        try:
            # Load and prepare image
            image_b64 = load_test_image(image_path)
            
            # Test /detect_face endpoint
            print("   🔍 Testing /detect_face...")
            detect_response = session.post(
                f"{base_url}/detect_face",
                json={'image': image_b64},
                headers={'Content-Type': 'application/json'}
            )
            
            if detect_response.status_code == 200:
                detect_data = detect_response.json()
                detect_faces = detect_data.get('faces', [])
                detect_count = len(detect_faces)
                print(f"      ✅ Detected {detect_count} faces")
                if detect_faces:
                    for i, face in enumerate(detect_faces):
                        print(f"         Face {i+1}: {face.get('display_name', 'Unknown')} ({face.get('status', 'unknown')})")
            else:
                print(f"      ❌ Error: {detect_response.status_code}")
                detect_count = 0
                detect_faces = []
            
            # Test /recognize endpoint (only if authenticated)
            if use_auth:
                print("   🎯 Testing /recognize...")
                recognize_response = session.post(
                    f"{base_url}/recognize",
                    json={'image': image_b64},
                    headers={'Content-Type': 'application/json'}
                )
                
                if recognize_response.status_code == 200:
                    recognize_data = recognize_response.json()
                    recognized = recognize_data.get('recognized', False)
                    message = recognize_data.get('message', 'No message')
                    print(f"      ✅ Recognition result: {recognized}")
                    print(f"         Message: {message}")
                    
                    # Compare consistency
                    if detect_count > 0 and recognized:
                        print("      ✅ CONSISTENT: Both endpoints detected/recognized face")
                    elif detect_count == 0 and not recognized:
                        print("      ✅ CONSISTENT: Both endpoints found no face")
                    elif detect_count > 0 and not recognized:
                        print("      ⚠️ INCONSISTENT: Face detected but not recognized (this was the bug)")
                    else:
                        print("      ⚠️ INCONSISTENT: Recognized without detection")
                        
                elif recognize_response.status_code == 400:
                    recognize_data = recognize_response.json()
                    error_msg = recognize_data.get('error', 'Unknown error')
                    print(f"      ℹ️ Recognition failed: {error_msg}")
                    
                    # If /detect_face found faces but /recognize failed, check why
                    if detect_count > 0:
                        if "No face detected" in error_msg:
                            print("      ❌ INCONSISTENT: detect_face found faces but recognize didn't")
                        elif "Multiple faces" in error_msg:
                            print("      ✅ CONSISTENT: Multiple faces correctly blocked for attendance")
                        else:
                            print(f"      ⚠️ INCONSISTENT: Different failure reasons")
                    else:
                        print("      ✅ CONSISTENT: Both failed to detect faces")
                else:
                    print(f"      ❌ Error: {recognize_response.status_code}")
            else:
                print("   ⚠️ Skipping /recognize test (not authenticated)")
                
        except Exception as e:
            print(f"   ❌ Error testing {filename}: {e}")
    
    print("\n🏁 Consistency test complete!")

if __name__ == "__main__":
    test_endpoint_consistency()
