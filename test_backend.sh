#!/bin/bash

echo "=== BACKEND HEALTH CHECK ==="
echo ""

echo "1. Health Check..."
curl -s http://localhost:5000/api/health
echo ""
echo ""

echo "2. Testing Authentication..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
else
  echo "✅ Token obtained: ${TOKEN:0:30}..."
  echo ""
  
  echo "3. Testing Schedule Endpoint..."
  RESPONSE=$(curl -s "http://localhost:5000/api/schedule/time-slots?date=2025-11-02")
  echo "$RESPONSE" | jq '{success, slot_count: (.timeSlots | length)}'
  
  echo ""
  echo "4. Testing Appointment Creation..."
  curl -s -X POST http://localhost:5000/api/schedule/appointments \
    -H "Content-Type: application/json" \
    -d '{
      "applicant_name":"Test User",
      "applicant_email":"test@test.com",
      "applicant_phone":"+251912345678",
      "scheduled_date":"2025-11-02",
      "scheduled_time":"09:00",
      "notes":"Backend test"
    }' | jq '.'
  
  echo ""
  echo "5. Verifying Slot Marked as Booked..."
  curl -s "http://localhost:5000/api/schedule/time-slots?date=2025-11-02" | \
    jq '.timeSlots[] | select(.time == "09:00") | {time, label, available}'
fi

echo ""
echo "=== TEST COMPLETE ==="

