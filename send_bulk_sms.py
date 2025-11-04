#!/usr/bin/env python3
"""
Send bulk SMS to all contacts from CSV file
Supports multiple methods:
1. ADB (Android Debug Bridge) - uses your phone directly
2. SMS API (AfroMessage) - uses SMS service
"""

import csv
import subprocess
import time
import sys
import os
from typing import List, Tuple

def normalize_phone_for_sms(phone: str) -> str:
    """Normalize phone number for SMS (add country code if needed)"""
    phone = phone.strip()
    # If it starts with 0, convert to +251 format
    if phone.startswith('0'):
        return '+251' + phone[1:]
    elif phone.startswith('251'):
        return '+' + phone
    elif phone.startswith('+251'):
        return phone
    else:
        # Assume it's already in correct format or add +251
        return '+251' + phone

def send_sms_via_adb(phone: str, message: str) -> Tuple[bool, str]:
    """Send SMS using ADB (Android Debug Bridge)"""
    try:
        # Normalize phone number
        phone_normalized = normalize_phone_for_sms(phone)
        
        # Escape message for shell
        message_escaped = message.replace('"', '\\"').replace('$', '\\$')
        
        # Use ADB to send SMS via Android's messaging app
        # This requires the phone to be connected via USB with USB debugging enabled
        cmd = [
            'adb', 'shell', 'am', 'start',
            '-a', 'android.intent.action.SENDTO',
            '-d', f'sms:{phone_normalized}',
            '--es', 'sms_body', message_escaped,
            '--ez', 'exit_on_sent', 'true'
        ]
        
        # Alternative: Use service call (requires root or specific permissions)
        # This is more direct but needs proper setup
        # For now, we'll use the intent method which opens the messaging app
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True, "SMS intent sent"
        else:
            return False, result.stderr or result.stdout
            
    except subprocess.TimeoutExpired:
        return False, "ADB command timed out"
    except FileNotFoundError:
        return False, "ADB not found. Install Android SDK Platform Tools or use SMS API method"
    except Exception as e:
        return False, str(e)

def send_sms_via_api(phone: str, message: str, api_key: str, sender_id: str, base_url: str = "https://api.afromessage.com") -> Tuple[bool, str]:
    """Send SMS using SMS API (AfroMessage)"""
    try:
        import requests
        
        # Normalize phone number
        phone_normalized = normalize_phone_for_sms(phone)
        
        endpoint = f"{base_url}/api/send"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'to': phone_normalized,
            'message': message,
        }
        
        if sender_id:
            payload['from'] = sender_id
        
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        
        if 200 <= resp.status_code < 300:
            try:
                response_data = resp.json()
                if response_data.get('acknowledge') == 'error':
                    return False, str(response_data.get('response', {}).get('errors', []))
                return True, "SMS sent successfully"
            except:
                return True, "SMS sent successfully"
        else:
            return False, f"API returned {resp.status_code}: {resp.text}"
            
    except Exception as e:
        return False, str(e)

def send_bulk_sms(csv_file: str, message: str, method: str = "adb", delay: float = 2.0, 
                  api_key: str = None, sender_id: str = None, base_url: str = None):
    """Send SMS to all contacts in CSV file"""
    
    contacts = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip().strip('"')
            phone = row['phone'].strip()
            if name and phone:
                contacts.append((name, phone))
    
    print(f"📱 Found {len(contacts)} contacts in {csv_file}")
    print(f"📝 Message: {message[:50]}..." if len(message) > 50 else f"📝 Message: {message}")
    print(f"🔧 Method: {method.upper()}")
    print(f"⏱️  Delay between messages: {delay} seconds")
    print()
    
    # Confirm before sending
    response = input(f"⚠️  Send SMS to {len(contacts)} contacts? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cancelled")
        return
    
    # Check ADB connection if using ADB method
    if method == "adb":
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            if 'device' not in result.stdout:
                print("❌ No Android device connected via ADB")
                print("   Please:")
                print("   1. Connect your phone via USB")
                print("   2. Enable USB debugging (Settings > Developer options)")
                print("   3. Run: adb devices")
                return
            print("✅ Android device detected via ADB")
        except FileNotFoundError:
            print("❌ ADB not found")
            print("   Install Android SDK Platform Tools:")
            print("   - Linux: sudo apt install android-tools-adb")
            print("   - Mac: brew install android-platform-tools")
            print("   - Or download from: https://developer.android.com/studio/releases/platform-tools")
            return
    
    # Send SMS
    successful = 0
    failed = 0
    
    for i, (name, phone) in enumerate(contacts, 1):
        print(f"[{i}/{len(contacts)}] Sending to {name} ({phone})...", end=' ')
        
        if method == "adb":
            success, error = send_sms_via_adb(phone, message)
        elif method == "api":
            if not api_key:
                print("❌ API key required for API method")
                return
            success, error = send_sms_via_api(phone, message, api_key, sender_id, base_url)
        else:
            print(f"❌ Unknown method: {method}")
            return
        
        if success:
            print("✅")
            successful += 1
        else:
            print(f"❌ {error}")
            failed += 1
        
        # Delay between messages (except for last one)
        if i < len(contacts):
            time.sleep(delay)
    
    print()
    print("=" * 50)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(contacts)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Send bulk SMS to contacts from CSV')
    parser.add_argument('csv_file', help='CSV file with contacts (name, phone)')
    parser.add_argument('message', help='SMS message to send')
    parser.add_argument('--method', choices=['adb', 'api'], default='adb',
                       help='Method to use: adb (Android phone) or api (SMS service)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between messages in seconds (default: 2.0)')
    
    # API options
    parser.add_argument('--api-key', help='SMS API key (required for API method)')
    parser.add_argument('--sender-id', help='SMS sender ID (optional for API method)')
    parser.add_argument('--base-url', default='https://api.afromessage.com',
                       help='SMS API base URL (default: https://api.afromessage.com)')
    
    args = parser.parse_args()
    
    send_bulk_sms(
        args.csv_file,
        args.message,
        method=args.method,
        delay=args.delay,
        api_key=args.api_key,
        sender_id=args.sender_id,
        base_url=args.base_url
    )

