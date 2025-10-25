#!/usr/bin/env python3
"""
Local development server for Soupie
Run this script to start the Flask development server
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

# Import and run the Flask app
if __name__ == '__main__':
    try:
        from api.app import app
        print("Starting Soupie development server...")
        print("Server will be available at: http://localhost:5000")
        print("Auto-reload enabled for development")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print("Error importing Flask app:")
        print(f"   {e}")
        print("\nMake sure you've installed dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
