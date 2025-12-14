"""Quick test script to verify the server is running"""
import requests
import time
import sys

print("Testing server connection...")
time.sleep(2)  # Wait for server to start

try:
    response = requests.get('http://localhost:5000', timeout=5)
    if response.status_code == 200:
        print("✓ Server is running successfully!")
        print(f"✓ Status Code: {response.status_code}")
        print("✓ You can now access the application at http://localhost:5000")
        sys.exit(0)
    else:
        print(f"✗ Server returned status code: {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to server. Make sure the server is running.")
    print("  Run: python app_web.py")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

