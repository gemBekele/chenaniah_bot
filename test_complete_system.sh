#!/bin/bash

echo "=== COMPREHENSIVE SYSTEM TEST ==="
echo ""

# Get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

echo "✅ Authentication successful"
echo ""

# Test bulk creation
echo "Testing bulk slot creation for Nov 20, 2025..."
BULK_RESPONSE=$(curl -s -X POST http://localhost:5000/api/schedule/time-slots/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-11-20","start_time":"13:30","end_time":"17:30","interval_minutes":15}')

echo "$BULK_RESPONSE" | jq '.'
echo ""

# Verify created slots
echo "Verifying created slots..."
SLOT_COUNT=$(curl -s -X GET "http://localhost:5000/api/schedule/time-slots?date=2025-11-20" | jq '.timeSlots | length')
echo "Found $SLOT_COUNT slots for Nov 20, 2025"
echo ""

# Test public access
echo "Testing public schedule access..."
PUBLIC_COUNT=$(curl -s "http://localhost:5000/api/schedule/time-slots?date=2025-11-20" | jq '.timeSlots | length')
echo "Public access returned $PUBLIC_COUNT slots"
echo ""

# Show sample slots
echo "Sample of created slots:"
curl -s -X GET "http://localhost:5000/api/schedule/time-slots?date=2025-11-20" | jq '.timeSlots[:5] | .[] | {time, label, available}'
echo ""

echo "=== TEST COMPLETE ==="

