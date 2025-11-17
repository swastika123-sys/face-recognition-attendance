#!/usr/bin/env python3
"""
Flask Application Launcher
==========================

This script provides a clean way to start the Flask application
without the confusion of auto-reload restarts.

Usage:
    python3 start_app.py

Features:
- Clear startup messages
- No auto-reload confusion
- Process monitoring
- Easy restart instructions
"""

import os
import sys
import subprocess
from pathlib import Path

def start_flask_app():
    """Start the Flask application with clear messaging"""
    
    print("=" * 60)
    print("🚀 FACE RECOGNITION ATTENDANCE SYSTEM")
    print("=" * 60)
    print()
    
    # Change to the correct directory
    app_dir = Path(__file__).parent.absolute()
    os.chdir(app_dir)
    
    print(f"📁 Working directory: {app_dir}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print()
    
    # Check if app.py exists
    if not Path("app.py").exists():
        print("❌ ERROR: app.py not found in current directory!")
        return
    
    print("🔧 Starting Flask application...")
    print("   - Debug mode: ON")
    print("   - Auto-reload: DISABLED (prevents restart confusion)")
    print("   - Port: 5001")
    print("   - Host: localhost")
    print()
    print("🌐 Access URLs:")
    print("   - Local: http://localhost:5001")
    print("   - Network: http://127.0.0.1:5001")
    print()
    print("💡 Features available:")
    print("   ✅ Teacher registration (secret: 'admin')")
    print("   ✅ Student registration with face capture")
    print("   ✅ Face recognition attendance")
    print("   ✅ Manual attendance management")
    print("   ✅ Database-only duplicate detection")
    print()
    print("🛑 To stop the server: Press Ctrl+C")
    print("=" * 60)
    print()
    
    try:
        # Start the Flask app
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n")
        print("🛑 Server stopped by user")
        print("✨ Thanks for using Face Recognition Attendance System!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("💡 Try running 'python3 app.py' directly")

if __name__ == "__main__":
    start_flask_app()
