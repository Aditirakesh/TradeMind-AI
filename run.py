"""
TradeMind AI — Quick Launcher
Author: Aditi
Run this script to start the Streamlit chatbot app.
Usage: python run.py
"""

import subprocess
import sys
import os

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(project_root, "app", "app.py")

    print("Starting TradeMind AI...")
    print(f"   App: {app_path}")
    print(f"   URL: http://localhost:8501")
    print()

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", app_path,
         "--server.port", "8501",
         "--server.headless", "true"],
        cwd=project_root
    )

if __name__ == "__main__":
    main()
