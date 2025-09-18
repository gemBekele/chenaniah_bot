#!/bin/bash

# VPS Deployment Script for Chenaniah Bot
# Run this script on your VPS

echo "🚀 Starting Chenaniah Bot VPS Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Don't run this script as root! Use your regular user account."
    exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx htop curl wget -y

# Create bot directory
print_status "Creating bot directory..."
mkdir -p ~/chenaniah-bot
cd ~/chenaniah-bot

# Clone repository if not exists
if [ ! -d ".git" ]; then
    print_status "Cloning repository..."
    git clone https://github.com/gemBekele/chenaniah_bot.git .
else
    print_status "Repository already exists, pulling latest changes..."
    git pull origin main
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data temp exports audio_files

# Set up environment file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment file..."
    cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Google Drive (optional - bot will use local storage if not set)
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_SHEET_ID=your_sheet_id_here

# Database
DATABASE_PATH=./vocalist_screening.db

# Server
BASE_URL=https://15.204.227.47
PORT=5000
EOF
    print_warning "Please edit .env file with your actual values:"
    print_warning "nano .env"
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/chenaniah-bot.service > /dev/null << EOF
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
print_status "Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/chenaniah-bot > /dev/null << EOF
server {
    listen 80;
    server_name 15.204.227.47;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /audio_files/ {
        alias $(pwd)/audio_files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable Nginx site
print_status "Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/chenaniah-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    print_status "Nginx configuration is valid"
    sudo systemctl reload nginx
else
    print_error "Nginx configuration has errors!"
    exit 1
fi

# Enable and start the bot service
print_status "Enabling bot service..."
sudo systemctl daemon-reload
sudo systemctl enable chenaniah-bot

print_status "Deployment completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit your environment variables:"
echo "   nano .env"
echo ""
echo "2. Start the bot:"
echo "   sudo systemctl start chenaniah-bot"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status chenaniah-bot"
echo ""
echo "4. View logs:"
echo "   journalctl -u chenaniah-bot -f"
echo ""
echo "5. Test the bot:"
echo "   curl http://15.204.227.47"
echo ""
echo "6. (Optional) Set up SSL:"
echo "   sudo certbot --nginx -d 15.204.227.47"
echo ""
print_status "Your bot will be available at: http://15.204.227.47"
