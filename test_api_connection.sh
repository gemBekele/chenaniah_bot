#!/bin/bash

echo "🌐 Testing API server connection..."

# Test if API server is running
echo "1. Testing API health endpoint..."
curl -s http://localhost:5000/api/health || echo "❌ API server not responding"

echo ""
echo "2. Testing API login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "Login response: $LOGIN_RESPONSE"

# Extract token if login successful
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
    echo "✅ Login successful, token: ${TOKEN:0:20}..."
    
    echo ""
    echo "3. Testing API submissions endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/submissions | head -c 500
    echo ""
    
    echo ""
    echo "4. Testing API stats endpoint..."
    curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/stats
    echo ""
else
    echo "❌ Login failed"
fi

echo ""
echo "5. Checking if API server process is running..."
ps aux | grep gunicorn | grep -v grep || echo "❌ No gunicorn process found"

echo ""
echo "6. Checking API server port..."
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not listening"
