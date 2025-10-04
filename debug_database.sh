#!/bin/bash

echo "🔍 Deploying database diagnostic tools to VPS..."

# Configuration - UPDATE THESE VALUES
VPS_IP="YOUR_VPS_IP_HERE"
VPS_USER="barch"

echo "⚠️  IMPORTANT: Update the VPS_IP variable in this script first!"
echo ""
echo "Current configuration:"
echo "  VPS IP: $VPS_IP"
echo "  VPS User: $VPS_USER"
echo ""

if [ "$VPS_IP" = "YOUR_VPS_IP_HERE" ]; then
    echo "❌ Please update VPS_IP in the script first!"
    exit 1
fi

read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Copy diagnostic scripts
echo "📦 Copying diagnostic scripts..."
scp check_database.py $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/
scp test_api_direct.py $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/

echo "✅ Diagnostic scripts copied"
echo ""

# Run diagnostics on VPS
echo "🔍 Running database diagnostics on VPS..."
ssh $VPS_USER@$VPS_IP "
    echo 'Running database diagnostics...'
    cd /home/$VPS_USER/chenaniah_bot
    source venv/bin/activate
    
    echo ''
    echo '=== DATABASE CONTENTS CHECK ==='
    python check_database.py
    
    echo ''
    echo '=== API DATABASE CONNECTION TEST ==='
    python test_api_direct.py
    
    echo ''
    echo '=== API SERVER STATUS ==='
    sudo systemctl status chenaniah-api --no-pager -l
    
    echo ''
    echo '=== API SERVER LOGS (last 20 lines) ==='
    sudo journalctl -u chenaniah-api -n 20 --no-pager
    
    echo ''
    echo '=== BOT SERVICE STATUS ==='
    sudo systemctl status chenaniah-bot --no-pager -l
    
    echo ''
    echo '=== BOT LOGS (last 20 lines) ==='
    sudo journalctl -u chenaniah-bot -n 20 --no-pager
"

echo ""
echo "======================================"
echo "🔍 DIAGNOSTIC COMPLETE!"
echo "======================================"
echo ""
echo "Check the output above to see:"
echo "1. If submissions exist in the database"
echo "2. If the API can read from the database"
echo "3. If both services are running properly"
echo "4. If there are any errors in the logs"
