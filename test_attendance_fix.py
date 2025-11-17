#!/usr/bin/env python3
"""
Test script specifically for the attendance capture fix.
Tests the consistency between /detect_face and /recognize endpoints.
"""

import requests
import base64
import io
from PIL import Image, ImageDraw
import json

def create_test_face_image():
    """Create a simple test image with a face-like shape"""
    img = Image.new('RGB', (400, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple face
    # Head (circle)
    draw.ellipse([100, 100, 300, 300], fill='peachpuff', outline='black', width=2)
    
    # Eyes
    draw.ellipse([140, 160, 170, 190], fill='black')
    draw.ellipse([230, 160, 260, 190], fill='black')
    
    # Nose
    draw.polygon([(200, 200), (190, 230), (210, 230)], fill='pink')
    
    # Mouth
    draw.arc([170, 240, 230, 280], 0, 180, fill='red', width=3)
    
    return img

def image_to_base64(img):
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{img_data}'

def test_endpoint_consistency():
    """Test that both endpoints work consistently"""
    print("\n🧪 Testing Attendance Capture Fix")
    print("=" * 50)
    
    # Create test image
    test_img = create_test_face_image()
    img_data = image_to_base64(test_img)
    
    print("📸 Created test face image")
    
    # Test /detect_face endpoint
    print("\n1️⃣ Testing /detect_face endpoint...")
    try:
        response = requests.post(
            'http://localhost:5001/detect_face',
            json={'image': img_data},
            timeout=10
        )
        detect_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Faces detected: {len(detect_data.get('faces', []))}")
        print(f"   Response: {detect_data}")
        
        detect_success = response.status_code == 200 and len(detect_data.get('faces', [])) > 0
        print(f"   ✅ /detect_face: {'SUCCESS' if detect_success else 'FAILED'}")
        
    except Exception as e:
        print(f"   ❌ /detect_face error: {e}")
        detect_success = False
    
    # First login as teacher to test /recognize
    print("\n🔐 Logging in as teacher...")
    login_data = {
        'username': 'test_teacher',
        'password': 'test123'
    }
    
    session = requests.Session()
    try:
        login_response = session.post('http://localhost:5001/login', data=login_data, timeout=10)
        login_success = login_response.status_code in [200, 302]
        print(f"   Login status: {'SUCCESS' if login_success else 'FAILED'}")
    except Exception as e:
        print(f"   Login error: {e}")
        login_success = False
    
    # Test /recognize endpoint
    print("\n2️⃣ Testing /recognize endpoint...")
    try:
        response = session.post(
            'http://localhost:5001/recognize',
            json={'image': img_data},
            timeout=10
        )
        recognize_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {recognize_data}")
        
        # Check if we get a proper response (either recognition success or "no match found")
        recognize_success = (
            response.status_code == 200 or 
            (response.status_code == 400 and "No face detected" not in recognize_data.get('error', ''))
        )
        print(f"   ✅ /recognize: {'SUCCESS' if recognize_success else 'FAILED'}")
        
    except Exception as e:
        print(f"   ❌ /recognize error: {e}")
        recognize_success = False
    
    # Final assessment
    print("\n📊 CONSISTENCY TEST RESULTS:")
    print("=" * 50)
    
    if detect_success and recognize_success:
        print("🎉 SUCCESS! Both endpoints are working consistently")
        print("✅ /detect_face can detect faces")
        print("✅ /recognize can process the same faces")
        print("✅ The attendance capture issue should be FIXED!")
    elif detect_success and not recognize_success:
        print("⚠️  PARTIAL SUCCESS: Detection works but recognition has issues")
        print("   This suggests the endpoints still have some inconsistency")
    elif not detect_success and not recognize_success:
        print("❌ BOTH ENDPOINTS FAILED: There may be a deeper issue")
    else:
        print("🤔 UNEXPECTED: Recognition works but detection doesn't")
    
    return detect_success and recognize_success

if __name__ == "__main__":
    test_endpoint_consistency()
