#!/usr/bin/env python3
"""
Face Recognition Attendance System - Launcher Script

This script:
1. Activates the venv-py311 virtual environment
2. Runs the Flask application (app.py)

Usage:
    python3 run_app.py
    OR
    ./run_app.py (if made executable with: chmod +x run_app.py)
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the project directory (where this script is located)
    project_dir = Path(__file__).parent.absolute()
    
    # Path to the virtual environment
    venv_dir = project_dir / "venv-py311"
    
    # Path to the Python interpreter in the virtual environment
    venv_python = venv_dir / "bin" / "python3"
    
    # Path to app.py
    app_file = project_dir / "app.py"
    
    # Check if virtual environment exists
    if not venv_dir.exists():
        print(f"❌ Error: Virtual environment not found at {venv_dir}")
        print("Please create the virtual environment first:")
        print("  python3.11 -m venv venv-py311")
        sys.exit(1)
    
    # Check if Python interpreter exists in venv
    if not venv_python.exists():
        print(f"❌ Error: Python interpreter not found at {venv_python}")
        print("Virtual environment may be corrupted. Try recreating it.")
        sys.exit(1)
    
    # Check if app.py exists
    if not app_file.exists():
        print(f"❌ Error: app.py not found at {app_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Face Recognition Attendance System")
    print("=" * 60)
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Virtual environment: {venv_dir}")
    print(f"▶️  Running: {app_file}")
    print("=" * 60)
    print()
    
    # Change to project directory
    os.chdir(project_dir)
    
    # Run the Flask app using the virtual environment's Python
    # This automatically uses the venv's packages without needing to source activate
    try:
        # Use subprocess to run the app with the venv Python
        result = subprocess.run(
            [str(venv_python), str(app_file)],
            cwd=str(project_dir),
            env=os.environ.copy()  # Pass current environment variables
        )
        
        # Exit with the same code as the Flask app
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
