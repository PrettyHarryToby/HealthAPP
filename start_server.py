"""
Server startup script with error handling and diagnostics
"""
import sys
import socket

def check_port(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0  # True if port is available

def main():
    print("\n" + "="*60)
    print("Avenara - Web Server")
    print("="*60)
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    try:
        import flask
        import sqlalchemy
        print("✓ Flask and SQLAlchemy found")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Check port availability
    print("\nChecking port 5000...")
    if not check_port(5000):
        print("✗ Port 5000 is already in use!")
        print("\nOptions:")
        print("  1. Close the application using port 5000")
        print("  2. Use a different port (edit app_web.py, change port=5000 to port=5001)")
        sys.exit(1)
    else:
        print("✓ Port 5000 is available")
    
    # Import and start app
    print("\nStarting server...")
    print("="*60)
    print("Open your browser and navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*60)
    print()
    
    try:
        from app_web import app
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if all dependencies are installed: pip install -r requirements.txt")
        print("  2. Verify database file exists: health_database.db")
        print("  3. Check for syntax errors: python -m py_compile app_web.py")
        sys.exit(1)

if __name__ == '__main__':
    main()

