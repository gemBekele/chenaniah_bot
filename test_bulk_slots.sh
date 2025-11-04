#!/bin/bash

# Test bulk slot creation
echo "=== Testing Bulk Slot Creation ==="
echo ""

# Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"       }' | jq -r '.token')

echo "Testing bulk slot creation for Oct 30, afternoon 1:30-5:30, 15 min each"
echo ""

# Create bulk slots
curl -s -X POST http://localhost:5000/api/schedule/time-slots/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-30",
    "start_time": "13:30",
    "end_time": "17:30",
    "interval_minutes": 15
  }' | jq '.'

echo ""
echo "=== Test Complete ==="

