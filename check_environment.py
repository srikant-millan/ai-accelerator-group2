#!/usr/bin/env python3
"""
Quick script to check if the environment is set up correctly
"""
import sys
import os

print("=" * 60)
print("Environment Check")
print("=" * 60)

print(f"\nPython executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not in virtual environment')}")

print("\n" + "=" * 60)
print("Checking required packages...")
print("=" * 60)

packages = {
    'streamlit': 'Streamlit',
    'openai': 'OpenAI',
    'jira': 'JIRA',
    'requests': 'Requests',
    'python-dotenv': 'python-dotenv'
}

all_ok = True
for package, name in packages.items():
    try:
        if package == 'python-dotenv':
            import dotenv
            print(f"✅ {name}: {dotenv.__version__ if hasattr(dotenv, '__version__') else 'installed'}")
        elif package == 'jira':
            import jira
            print(f"✅ {name}: {jira.__version__ if hasattr(jira, '__version__') else 'installed'}")
        elif package == 'streamlit':
            import streamlit
            print(f"✅ {name}: {streamlit.__version__}")
        elif package == 'openai':
            import openai
            print(f"✅ {name}: {openai.__version__}")
        elif package == 'requests':
            import requests
            print(f"✅ {name}: {requests.__version__}")
    except ImportError as e:
        print(f"❌ {name}: NOT INSTALLED - {str(e)}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ All packages are installed correctly!")
    print("\nYou can run Streamlit with:")
    print("  streamlit run app.py")
else:
    print("❌ Some packages are missing!")
    print("\nTo install missing packages, run:")
    print("  pip install -r requirements.txt")
print("=" * 60)

