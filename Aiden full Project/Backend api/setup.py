import os
import sys
from pathlib import Path

def setup_project():
    """Setup the project structure"""
    
    print("🏗️  Setting up Multi-City Permits System")
    print("=" * 50)
    
    # Create directory structure
    directories = [
        'database',
        'scrapers',
        'models',
        'config',
        'utils',
        'templates',
        'static',
        'logs',
        'tests'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Create __init__.py files
    init_files = [
        'database/__init__.py',
        'scrapers/__init__.py',
        'models/__init__.py',
        'config/__init__.py',
        'utils/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch(exist_ok=True)
        print(f"📄 Created file: {init_file}")
        

setup_project()