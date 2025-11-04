# Sending Bulk SMS from Terminal

There are two main methods to send SMS to all contacts from your phone:

## Method 1: ADB (Android Debug Bridge) - Recommended

This uses your Android phone directly via USB.

### Setup:
1. **Install ADB:**
   ```bash
   # Linux
   sudo apt install android-tools-adb
   
   # Mac
   brew install android-platform-tools
   
   # Or download from: https://developer.android.com/studio/releases/platform-tools
   ```

2. **Enable USB Debugging on your phone:**
   - Settings > About Phone > Tap "Build Number" 7 times
   - Settings > Developer Options > Enable "USB Debugging"
   - Connect phone via USB

3. **Verify connection:**
   ```bash
   adb devices
   ```
   Should show your device listed.

### Usage:

**Option A: Using the Python script (recommended)**
```bash
python3 send_bulk_sms.py applicants_processed.csv "Your message here" --method adb --delay 2
```

**Option B: Using the shell script for single SMS**
```bash
chmod +x send_sms_adb.sh
./send_sms_adb.sh 0911598384 "Test message"
```

**Option C: Simple loop (manual control)**
```bash
# Read CSV and send SMS one by one
while IFS=',' read -r name phone; do
    # Skip header
    [[ "$name" == "name" ]] && continue
    
    # Remove quotes and clean
    phone=$(echo "$phone" | tr -d '"' | tr -d ' ')
    
    echo "Sending to $name ($phone)..."
    adb shell am start -a android.intent.action.SENDTO \
        -d "sms:+251${phone:1}" \
        --es sms_body "Your message here" \
        --ez exit_on_sent true
    
    sleep 2  # Delay between messages
done < applicants_processed.csv
```

## Method 2: SMS API (AfroMessage)

This uses the SMS service API (requires API key).

### Setup:
1. Get your API credentials from your SMS provider
2. Set environment variables or pass as arguments

### Usage:
```bash
python3 send_bulk_sms.py applicants_processed.csv "Your message here" \
    --method api \
    --api-key YOUR_API_KEY \
    --sender-id YOUR_SENDER_ID \
    --delay 1
```

Or create a `.env` file:
```bash
AFROMESSAGE_API_KEY=your_key_here
AFROMESSAGE_SENDER_ID=your_sender_id
AFROMESSAGE_BASE_URL=https://api.afromessage.com
```

Then use:
```bash
python3 send_bulk_sms.py applicants_processed.csv "Your message here" --method api
```

## Quick Start (ADB Method)

```bash
# 1. Make script executable
chmod +x send_bulk_sms.py

# 2. Connect your phone and verify
adb devices

# 3. Send SMS to all contacts
python3 send_bulk_sms.py applicants_processed.csv "Hello! This is a test message from Chenaniah." --method adb --delay 2
```

## Notes:

- **ADB Method**: Opens the messaging app on your phone for each message. You may need to manually tap send on some phones, or it may auto-send depending on your messaging app.
- **Delay**: Use appropriate delay (2-5 seconds) to avoid rate limiting
- **Phone Format**: Scripts automatically convert `09xxxxxxxx` to `+2519xxxxxxxx` format
- **Testing**: Test with a single contact first before sending to all

## Troubleshooting:

**ADB not found:**
- Install Android Platform Tools (see Setup above)

**No device detected:**
- Check USB connection
- Enable USB debugging on phone
- Accept "Allow USB debugging" prompt on phone
- Try: `adb kill-server && adb start-server`

**SMS not sending:**
- Some phones require manual tap on send button
- Try different messaging app (Google Messages, Samsung Messages, etc.)
- Check phone permissions for SMS app

