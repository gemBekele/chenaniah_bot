#!/bin/bash
# Simple ADB-based SMS sender
# Usage: ./send_sms_adb.sh <phone_number> <message>

PHONE="$1"
MESSAGE="$2"

if [ -z "$PHONE" ] || [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <phone_number> <message>"
    echo "Example: $0 +251911598384 'Hello, this is a test message'"
    exit 1
fi

# Normalize phone: add +251 if it starts with 0
if [[ "$PHONE" =~ ^0 ]]; then
    PHONE="+251${PHONE:1}"
fi

# Send SMS using ADB
adb shell am start -a android.intent.action.SENDTO \
    -d "sms:${PHONE}" \
    --es sms_body "${MESSAGE}" \
    --ez exit_on_sent true

echo "SMS intent sent to ${PHONE}"

