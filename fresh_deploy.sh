#!/bin/bash

# Fresh VPS Deployment Script
# This script removes everything and deploys both web and bot applications

set -e  # Exit on any error

echo "======================================"
echo "🚀 FRESH VPS DEPLOYMENT"
echo "======================================"
echo "This will remove everything and deploy fresh"
echo ""

# Configuration
VPS_IP="15.204.227.47"
VPS_USER="barch"
WEB_DIR="/home/barch/projects/chenaniah/web/chenaniah-web"
BOT_DIR="/home/barch/chenaniah-bot"
NGINX_SITES_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run commands on VPS
run_on_vps() {
    ssh $VPS_USER@$VPS_IP "$1"
}

# Function to copy files to VPS
copy_to_vps() {
    scp -r "$1" $VPS_USER@$VPS_IP:"$2"
}

print_status "Starting fresh deployment to VPS $VPS_IP..."
echo ""

# Step 1: Connect and prepare VPS
print_status "Step 1: Preparing VPS environment..."

run_on_vps "
    # Update system
    echo 'Updating system packages...'
    sudo apt update -y
    sudo apt upgrade -y
    
    # Install required packages
    echo 'Installing required packages...'
    sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx nodejs npm curl wget htop
    
    # Create directories
    echo 'Creating directories...'
    mkdir -p ~/projects/chenaniah/web
    mkdir -p ~/chenaniah-bot
    mkdir -p ~/chenaniah-bot/logs
    mkdir -p ~/chenaniah-bot/audio_files
    mkdir -p ~/chenaniah-bot/data
    mkdir -p ~/chenaniah-bot/temp
    mkdir -p ~/chenaniah-bot/exports
"

print_success "VPS environment prepared"
echo ""

# Step 2: Stop existing services
print_status "Step 2: Stopping existing services..."

run_on_vps "
    # Stop bot service if running
    sudo systemctl stop chenaniah-bot 2>/dev/null || true
    sudo systemctl disable chenaniah-bot 2>/dev/null || true
    
    # Stop nginx
    sudo systemctl stop nginx 2>/dev/null || true
    
    # Kill any running processes
    pkill -f telegram_bot.py 2>/dev/null || true
    pkill -f run_bot.py 2>/dev/null || true
    pkill -f node 2>/dev/null || true
"

print_success "Existing services stopped"
echo ""

# Step 3: Clean up old files
print_status "Step 3: Cleaning up old files..."

run_on_vps "
    # Remove old bot files
    rm -rf ~/chenaniah-bot/*
    
    # Remove old web files
    rm -rf ~/projects/chenaniah/web/*
    
    # Remove old nginx configs
    sudo rm -f $NGINX_SITES_DIR/chenaniah-* 2>/dev/null || true
    sudo rm -f $NGINX_ENABLED_DIR/chenaniah-* 2>/dev/null || true
    
    # Clean nginx default
    sudo rm -f $NGINX_ENABLED_DIR/default 2>/dev/null || true
"

print_success "Old files cleaned up"
echo ""

# Step 4: Deploy Web Application
print_status "Step 4: Deploying Web Application..."

# Copy web application files
print_status "Copying web application files..."
copy_to_vps "/home/barch/projects/chenaniah/web/chenaniah-web" "/home/barch/projects/chenaniah/web/"

# Install web dependencies and build
run_on_vps "
    cd $WEB_DIR
    
    # Install dependencies
    npm install
    
    # Build the application
    npm run build
    
    # Create production start script
    cat > start-web.sh << 'EOF'
#!/bin/bash
cd $WEB_DIR
npm start
EOF
    
    chmod +x start-web.sh
"

print_success "Web application deployed and built"
echo ""

# Step 5: Deploy Bot Application
print_status "Step 5: Deploying Bot Application..."

# Copy bot files
print_status "Copying bot application files..."
copy_to_vps "/home/barch/projects/chenaniah/bot" "/home/barch/chenaniah-bot/"

# Setup bot environment
run_on_vps "
    cd $BOT_DIR
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs data temp exports audio_files
    
    # Set permissions
    chmod +x *.sh
    chmod +x *.py
"

print_success "Bot application deployed and configured"
echo ""

# Step 6: Configure Nginx
print_status "Step 6: Configuring Nginx..."

run_on_vps "
    # Create nginx configuration for web app
    sudo tee $NGINX_SITES_DIR/chenaniah-web << 'EOF'
server {
    listen 80;
    server_name $VPS_IP;
    
    # Web application
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Static files
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control 'public, immutable';
    }
    
    # Bot API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Audio files
    location /audio_files/ {
        alias /home/barch/chenaniah-bot/audio_files/;
        expires 1y;
        add_header Cache-Control 'public, immutable';
        
        # Enable CORS for audio files
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
        add_header Access-Control-Allow-Headers 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }
}
EOF

    # Enable the site
    sudo ln -sf $NGINX_SITES_DIR/chenaniah-web $NGINX_ENABLED_DIR/
    
    # Test nginx configuration
    sudo nginx -t
"

print_success "Nginx configured"
echo ""

# Step 7: Create Systemd Services
print_status "Step 7: Creating systemd services..."

# Create web service
run_on_vps "
    sudo tee /etc/systemd/system/chenaniah-web.service << 'EOF'
[Unit]
Description=Chenaniah Web Application
After=network.target

[Service]
Type=simple
User=barch
WorkingDirectory=$WEB_DIR
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

# Logging
StandardOutput=append:$WEB_DIR/logs/web.log
StandardError=append:$WEB_DIR/logs/web-error.log

[Install]
WantedBy=multi-user.target
EOF
"

# Create bot service
run_on_vps "
    sudo tee /etc/systemd/system/chenaniah-bot.service << 'EOF'
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=barch
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python telegram_bot_optimized.py

# Restart policy
Restart=always
RestartSec=10

# Performance settings
LimitNOFILE=65535
LimitNPROC=4096

# Logging
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF
"

print_success "Systemd services created"
echo ""

# Step 8: Run system optimizations
print_status "Step 8: Running system optimizations..."

run_on_vps "
    cd $BOT_DIR
    sudo bash optimize_vps.sh
"

print_success "System optimizations applied"
echo ""

# Step 9: Setup environment variables
print_status "Step 9: Setting up environment variables..."

run_on_vps "
    cd $BOT_DIR
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cat > .env << 'EOF'
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database
DATABASE_PATH=./vocalist_screening.db

# Server
BASE_URL=http://$VPS_IP
PORT=5000

# API
API_SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF
    fi
    
    echo '⚠️  IMPORTANT: Update .env file with your actual values!'
    echo '   - TELEGRAM_BOT_TOKEN'
    echo '   - API_SECRET_KEY'
    echo '   - ADMIN_PASSWORD'
"

print_warning "Environment variables template created - UPDATE REQUIRED!"
echo ""

# Step 10: Start services
print_status "Step 10: Starting services..."

run_on_vps "
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable chenaniah-web
    sudo systemctl enable chenaniah-bot
    sudo systemctl enable nginx
    
    # Start nginx
    sudo systemctl start nginx
    
    # Start web application
    sudo systemctl start chenaniah-web
    
    # Wait a moment for web to start
    sleep 5
    
    # Start bot (only if .env is configured)
    if grep -q 'your_bot_token_here' $BOT_DIR/.env; then
        echo '⚠️  Bot not started - please update .env file first'
    else
        sudo systemctl start chenaniah-bot
        echo '✅ Bot started successfully'
    fi
"

print_success "Services started"
echo ""

# Step 11: Verify deployment
print_status "Step 11: Verifying deployment..."

run_on_vps "
    echo '=== Service Status ==='
    sudo systemctl status chenaniah-web --no-pager -l
    echo ''
    sudo systemctl status chenaniah-bot --no-pager -l
    echo ''
    sudo systemctl status nginx --no-pager -l
    echo ''
    
    echo '=== Port Status ==='
    netstat -tlnp | grep -E ':(80|3000|5000)'
    echo ''
    
    echo '=== Disk Usage ==='
    df -h
    echo ''
    
    echo '=== Memory Usage ==='
    free -h
"

print_success "Deployment verification complete"
echo ""

# Step 12: Create management scripts
print_status "Step 12: Creating management scripts..."

run_on_vps "
    cd $BOT_DIR
    
    # Create start script
    cat > start-all.sh << 'EOF'
#!/bin/bash
echo 'Starting all Chenaniah services...'
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot
echo 'All services started!'
EOF
    
    # Create stop script
    cat > stop-all.sh << 'EOF'
#!/bin/bash
echo 'Stopping all Chenaniah services...'
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx
echo 'All services stopped!'
EOF
    
    # Create restart script
    cat > restart-all.sh << 'EOF'
#!/bin/bash
echo 'Restarting all Chenaniah services...'
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot
echo 'All services restarted!'
EOF
    
    # Create status script
    cat > status-all.sh << 'EOF'
#!/bin/bash
echo '=== Chenaniah Services Status ==='
echo ''
echo 'Nginx:'
sudo systemctl status nginx --no-pager -l
echo ''
echo 'Web App:'
sudo systemctl status chenaniah-web --no-pager -l
echo ''
echo 'Bot:'
sudo systemctl status chenaniah-bot --no-pager -l
echo ''
echo 'Ports:'
netstat -tlnp | grep -E ':(80|3000|5000)'
echo ''
echo 'Resources:'
free -h
df -h
EOF
    
    # Create logs script
    cat > logs-all.sh << 'EOF'
#!/bin/bash
echo '=== Chenaniah Services Logs ==='
echo ''
echo 'Web App Logs:'
journalctl -u chenaniah-web -n 20 --no-pager
echo ''
echo 'Bot Logs:'
journalctl -u chenaniah-bot -n 20 --no-pager
echo ''
echo 'Nginx Logs:'
journalctl -u nginx -n 20 --no-pager
EOF
    
    # Make scripts executable
    chmod +x *.sh
    
    echo 'Management scripts created:'
    echo '  - start-all.sh'
    echo '  - stop-all.sh'
    echo '  - restart-all.sh'
    echo '  - status-all.sh'
    echo '  - logs-all.sh'
"

print_success "Management scripts created"
echo ""

# Final summary
echo "======================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "✅ Web Application: http://$VPS_IP"
echo "✅ Bot API: http://$VPS_IP/api/"
echo "✅ Audio Files: http://$VPS_IP/audio_files/"
echo "✅ Health Check: http://$VPS_IP/health"
echo ""
echo "📁 Directories:"
echo "   Web: $WEB_DIR"
echo "   Bot: $BOT_DIR"
echo ""
echo "🔧 Management Commands:"
echo "   cd $BOT_DIR"
echo "   ./start-all.sh    # Start all services"
echo "   ./stop-all.sh     # Stop all services"
echo "   ./restart-all.sh  # Restart all services"
echo "   ./status-all.sh   # Check status"
echo "   ./logs-all.sh     # View logs"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Update $BOT_DIR/.env with your actual values:"
echo "   - TELEGRAM_BOT_TOKEN"
echo "   - API_SECRET_KEY"
echo "   - ADMIN_PASSWORD"
echo ""
echo "2. Start the bot:"
echo "   sudo systemctl start chenaniah-bot"
echo ""
echo "3. Test the deployment:"
echo "   curl http://$VPS_IP/health"
echo "   curl http://$VPS_IP/api/health"
echo ""
echo "4. Monitor logs:"
echo "   journalctl -u chenaniah-web -f"
echo "   journalctl -u chenaniah-bot -f"
echo ""
echo "🚀 Your Chenaniah platform is ready!"
echo "======================================"

