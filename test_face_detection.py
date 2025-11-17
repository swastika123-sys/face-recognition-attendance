#!/usr/bin/env python3

"""
Test script to verify face detection and multiple face prevention
"""

import requests
import base64
from PIL import Image, ImageDraw
import io
import numpy as np

def create_test_image_with_faces(num_faces=1, width=400, height=300):
    """Create a test image with simple face-like rectangles"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create simple rectangular "faces" at different positions
    face_size = 60
    positions = [
        (100, 100),  # First face
        (250, 150),  # Second face  
        (180, 200),  # Third face
    ]
    
    for i in range(min(num_faces, len(positions))):
        x, y = positions[i]
        # Draw a simple rectangle as a "face"
        draw.rectangle([x, y, x + face_size, y + face_size], fill='pink', outline='black', width=2)
        # Add some simple "eyes"
        draw.rectangle([x + 15, y + 20, x + 25, y + 30], fill='black')
        draw.rectangle([x + 35, y + 20, x + 45, y + 30], fill='black')
        # Add a "mouth"
        draw.rectangle([x + 25, y + 40, x + 35, y + 45], fill='black')
    
    return img

def test_face_detection(num_faces, description):
    """Test face detection with specified number of faces"""
    print(f"\n🧪 Testing: {description}")
    
    # Create test image
    img = create_test_image_with_faces(num_faces)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Test detect_face endpoint
    try:
        response = requests.post(
            'http://localhost:5001/detect_face', 
            json={'image': f'data:image/png;base64,{img_data}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            faces_count = data.get('total_faces', 0)
            print(f"   ✅ Detection Result: {faces_count} faces detected")
            
            for i, face in enumerate(data.get('faces', [])):
                print(f"   Face {i+1}: x={face['x']}, y={face['y']}, w={face['width']}, h={face['height']}")
                print(f"           Status: {face['status']}, Name: {face['display_name']}")
            
            return faces_count
        else:
            print(f"   ❌ Detection failed: {response.status_code} - {response.text}")
            return 0
            
    except Exception as e:
        print(f"   ❌ Detection error: {e}")
        return 0

def test_recognize_with_multiple_faces():
    """Test recognition endpoint with multiple faces to verify prevention"""
    print(f"\n🧪 Testing: Multiple face prevention in recognition")
    
    # Create test image with 2 faces
    img = create_test_image_with_faces(2)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Test recognize endpoint (this will fail due to login requirement, but we can see the response)
    try:
        response = requests.post(
            'http://localhost:5001/recognize', 
            json={'image': f'data:image/png;base64,{img_data}'},
            timeout=10
        )
        
        data = response.json()
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {data}")
        
        if 'multiple_faces' in data:
            print("   ✅ Multiple face prevention is working!")
        elif 'error' in data and 'Not logged in' in data['error']:
            print("   ⚠️  Need to be logged in to test full recognition flow")
        else:
            print("   ❓ Unclear if multiple face prevention is working")
            
    except Exception as e:
        print(f"   ❌ Recognition test error: {e}")

if __name__ == "__main__":
    print("🔬 Face Detection Testing Suite")
    print("=" * 50)
    
    # Test different scenarios
    test_face_detection(0, "No faces")
    test_face_detection(1, "Single face")
    test_face_detection(2, "Multiple faces")
    test_face_detection(3, "Three faces")
    
    # Test recognition with multiple faces
    test_recognize_with_multiple_faces()
    
    print("\n✅ Testing complete!")
