#!/bin/bash

echo "🚀 Deploying API server fix to VPS..."

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

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Please run this script from the bot directory"
    exit 1
fi

echo "✅ Found API server files"
echo ""

# Copy the updated API server file
echo "📦 Copying updated API server..."
scp api_server.py $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/

# Copy the WSGI file
echo "📦 Copying WSGI file..."
scp wsgi.py $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/

# Copy the service file
echo "📦 Copying service file..."
scp chenaniah-api.service $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/

# Copy the test script
echo "📦 Copying test script..."
scp test_api.py $VPS_USER@$VPS_IP:/home/$VPS_USER/chenaniah_bot/

echo "✅ Files copied successfully"
echo ""

# Deploy on VPS
echo "🚀 Deploying on VPS..."
ssh $VPS_USER@$VPS_IP "
    echo 'Setting up API server...'
    cd /home/$VPS_USER/chenaniah_bot
    
    # Install gunicorn if not already installed
    source venv/bin/activate
    pip install gunicorn
    
    # Copy service file to systemd
    sudo cp chenaniah-api.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable the service
    sudo systemctl enable chenaniah-api
    
    # Restart the API service
    sudo systemctl restart chenaniah-api
    
    # Check status
    echo 'API service status:'
    sudo systemctl status chenaniah-api --no-pager -l
    
    echo 'Testing API...'
    python test_api.py
    
    echo '✅ API server deployment completed!'
"

echo ""
echo "======================================"
echo "🎉 API SERVER FIX DEPLOYED!"
echo "======================================"
echo ""
echo "🌐 API is now available at:"
echo "   http://$VPS_IP:5000/api/health"
echo "   http://$VPS_IP:5000/api/submissions"
echo ""
echo "🔧 Management Commands:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   sudo systemctl status chenaniah-api"
echo "   sudo journalctl -u chenaniah-api -f"
echo ""
echo "🧪 Test the API:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   cd ~/chenaniah_bot"
echo "   python test_api.py"
echo ""
echo "✅ The API server should now show submissions from the bot!"
