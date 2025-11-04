#!/bin/bash

# Test scheduling endpoints
echo "=== Testing Scheduling Endpoints ==="
echo ""

# Login and get token
echo "1. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token"
  exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:20}..."
echo ""

# Set test date
TEST_DATE="2025-10-30"

# Test 2: Get current time slots
echo "2. Getting time slots for $TEST_DATE..."
curl -s -X GET "http://localhost:5000/api/schedule/time-slots?date=$TEST_DATE" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 3: Create a single time slot
echo "3. Creating a test time slot (14:30)..."
curl -s -X POST http://localhost:5000/api/schedule/time-slots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"time\":\"14:30\",\"date\":\"$TEST_DATE\"}" | jq '.'
echo ""

# Test 4: Create multiple time slots with 15-minute intervals
echo "4. Creating multiple 15-minute slots for afternoon (13:30-17:30)..."
START_HOUR=13
START_MIN=30
END_HOUR=17
END_MIN=30

for hour in $(seq $START_HOUR $END_HOUR); do
  if [ $hour -eq $START_HOUR ]; then
    start_min=$START_MIN
    end_min=60
  elif [ $hour -eq $END_HOUR ]; then
    start_min=0
    end_min=$END_MIN
  else
    start_min=0
    end_min=60
  fi
  
  for min in $(seq $start_min 15 $((end_min - 15))); do
    time_str=$(printf "%02d:%02d" $hour $min)
    echo "  Creating slot: $time_str"
    curl -s -X POST http://localhost:5000/api/schedule/time-slots \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"time\":\"$time_str\",\"date\":\"$TEST_DATE\"}" | jq -r '.success // "Failed"'
  done
done
echo ""

# Test 5: Get all time slots again
echo "5. Getting all time slots for $TEST_DATE after creation..."
curl -s -X GET "http://localhost:5000/api/schedule/time-slots?date=$TEST_DATE" \
  -H "Authorization: Bearer $TOKEN" | jq '.timeSlots | length'
echo " slots created"
echo ""

# Test 6: Create an appointment
echo "6. Creating a test appointment..."
curl -s -X POST http://localhost:5000/api/schedule/appointments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"applicant_name\": \"Test User\",
    \"applicant_email\": \"test@example.com\",
    \"applicant_phone\": \"+251912345678\",
    \"scheduled_date\": \"$TEST_DATE\",
    \"scheduled_time\": \"14:30\",
    \"notes\": \"Test appointment\"
  }" | jq '.'
echo ""

# Test 7: Get appointments
echo "7. Getting all appointments..."
curl -s -X GET http://localhost:5000/api/schedule/appointments \
  -H "Authorization: Bearer $TOKEN" | jq '.appointments | length'
echo " appointments found"
echo ""

# Test 8: Update appointment status
echo "8. Updating appointment status..."
APPOINTMENT_ID=$(curl -s -X GET http://localhost:5000/api/schedule/appointments \
  -H "Authorization: Bearer $TOKEN" | jq -r '.appointments[0].id')

if [ "$APPOINTMENT_ID" != "null" ] && [ -n "$APPOINTMENT_ID" ]; then
  curl -s -X PUT "http://localhost:5000/api/schedule/appointments/$APPOINTMENT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status":"completed"}' | jq '.'
else
  echo "No appointments found to update"
fi
echo ""

echo "=== All tests completed ==="

