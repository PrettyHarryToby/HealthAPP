#!/bin/bash
echo "========================================"
echo "Health Database Application - Web Server"
echo "========================================"
echo ""
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi
echo ""
echo "Starting web server..."
echo "Open your browser and navigate to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""
python3 app_web.py

