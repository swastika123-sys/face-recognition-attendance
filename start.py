#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

project_dir = Path(__file__).parent.absolute()
venv_python = project_dir / "venv-py311" / "bin" / "python3"
app_file = project_dir / "app.py"

os.chdir(project_dir)
subprocess.run([str(venv_python), str(app_file)])
