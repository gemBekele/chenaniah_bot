#!/bin/bash

# Git-based Deployment Script for Chenaniah Platform
# This script pulls latest changes and deploys both web and bot

set -e  # Exit on any error

echo "======================================"
echo "🚀 GIT-BASED DEPLOYMENT"
echo "======================================"
echo "This will pull latest changes and deploy"
echo ""

# Configuration
VPS_IP="15.204.227.47"
VPS_USER="barch"
WEB_DIR="/home/barch/projects/chenaniah/web/chenaniah-web"
BOT_DIR="/home/barch/chenaniah-bot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run from the project root."
    exit 1
fi

print_status "Starting git-based deployment to VPS $VPS_IP..."
echo ""

# Step 1: Pull latest changes locally
print_status "Step 1: Pulling latest changes locally..."

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes. Please commit or stash them first."
    git status --short
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled."
        exit 1
    fi
fi

# Pull latest changes
git pull origin main || git pull origin master || print_warning "Could not pull changes (no remote or different branch)"

print_success "Local repository updated"
echo ""

# Step 2: Connect to VPS and prepare
print_status "Step 2: Preparing VPS environment..."

ssh $VPS_USER@$VPS_IP "
    echo 'Preparing VPS environment...'
    
    # Update system packages
    echo 'Updating system packages...'
    sudo apt update -y
    sudo apt upgrade -y
    
    # Install required packages
    echo 'Installing required packages...'
    sudo apt install -y python3 python3-pip python3-venv git nginx nodejs npm curl wget htop
    
    # Create directories
    echo 'Creating directories...'
    mkdir -p ~/projects/chenaniah/web
    mkdir -p ~/chenaniah-bot
    mkdir -p ~/chenaniah-bot/logs
    mkdir -p ~/chenaniah-bot/audio_files
    mkdir -p ~/chenaniah-bot/data
    mkdir -p ~/chenaniah-bot/temp
    mkdir -p ~/chenaniah-bot/exports
    
    echo 'VPS environment prepared'
"

print_success "VPS environment prepared"
echo ""

# Step 3: Stop existing services
print_status "Step 3: Stopping existing services..."

ssh $VPS_USER@$VPS_IP "
    echo 'Stopping existing services...'
    
    # Stop services
    sudo systemctl stop chenaniah-bot 2>/dev/null || echo 'Bot service not running'
    sudo systemctl stop chenaniah-web 2>/dev/null || echo 'Web service not running'
    sudo systemctl stop nginx 2>/dev/null || echo 'Nginx not running'
    
    # Kill any running processes
    pkill -f telegram_bot.py 2>/dev/null || true
    pkill -f run_bot.py 2>/dev/null || true
    pkill -f node 2>/dev/null || true
    
    echo 'Services stopped'
"

print_success "Existing services stopped"
echo ""

# Step 4: Clone/Update repositories on VPS
print_status "Step 4: Setting up repositories on VPS..."

ssh $VPS_USER@$VPS_IP "
    echo 'Setting up repositories...'
    
    # Clone or update bot repository
    if [ -d ~/chenaniah-bot/.git ]; then
        echo 'Updating bot repository...'
        cd ~/chenaniah-bot
        git pull origin main || git pull origin master || echo 'Could not pull bot changes'
    else
        echo 'Cloning bot repository...'
        rm -rf ~/chenaniah-bot
        git clone https://github.com/gemBekele/chenaniah_bot.git ~/chenaniah-bot || {
            echo 'Could not clone bot repository. Creating from local files...'
            mkdir -p ~/chenaniah-bot
        }
    fi
    
    # Clone or update web repository
    if [ -d ~/projects/chenaniah/web/chenaniah-web/.git ]; then
        echo 'Updating web repository...'
        cd ~/projects/chenaniah/web/chenaniah-web
        git pull origin main || git pull origin master || echo 'Could not pull web changes'
    else
        echo 'Cloning web repository...'
        rm -rf ~/projects/chenaniah/web/chenaniah-web
        git clone https://github.com/gemBekele/chenaniah-web.git ~/projects/chenaniah/web/chenaniah-web || {
            echo 'Could not clone web repository. Creating from local files...'
            mkdir -p ~/projects/chenaniah/web/chenaniah-web
        }
    fi
    
    echo 'Repositories updated'
"

print_success "Repositories updated"
echo ""

# Step 5: Copy local files (as backup if git clone failed)
print_status "Step 5: Copying local files as backup..."

# Copy bot files
print_status "Copying bot files..."
scp -r . $VPS_USER@$VPS_IP:~/chenaniah-bot/

# Copy web files
print_status "Copying web files..."
scp -r ../web/chenaniah-web $VPS_USER@$VPS_IP:~/projects/chenaniah/web/

print_success "Local files copied"
echo ""

# Step 6: Setup bot application
print_status "Step 6: Setting up bot application..."

ssh $VPS_USER@$VPS_IP "
    echo 'Setting up bot application...'
    
    cd ~/chenaniah-bot
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs data temp exports audio_files
    
    # Set permissions
    chmod +x *.sh *.py
    
    echo 'Bot application setup complete'
"

print_success "Bot application setup complete"
echo ""

# Step 7: Setup web application
print_status "Step 7: Setting up web application..."

ssh $VPS_USER@$VPS_IP "
    echo 'Setting up web application...'
    
    cd ~/projects/chenaniah/web/chenaniah-web
    
    # Install dependencies
    npm install
    
    # Build the application
    npm run build
    
    echo 'Web application setup complete'
"

print_success "Web application setup complete"
echo ""

# Step 8: Configure Nginx
print_status "Step 8: Configuring Nginx..."

ssh $VPS_USER@$VPS_IP "
    echo 'Configuring Nginx...'
    
    # Create nginx configuration
    sudo tee /etc/nginx/sites-available/chenaniah << 'EOF'
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
    sudo ln -sf /etc/nginx/sites-available/chenaniah /etc/nginx/sites-enabled/
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    sudo nginx -t
    
    echo 'Nginx configured'
"

print_success "Nginx configured"
echo ""

# Step 9: Create systemd services
print_status "Step 9: Creating systemd services..."

ssh $VPS_USER@$VPS_IP "
    echo 'Creating systemd services...'
    
    # Create web service
    sudo tee /etc/systemd/system/chenaniah-web.service << 'EOF'
[Unit]
Description=Chenaniah Web Application
After=network.target

[Service]
Type=simple
User=barch
WorkingDirectory=/home/barch/projects/chenaniah/web/chenaniah-web
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/barch/projects/chenaniah/web/chenaniah-web/logs/web.log
StandardError=append:/home/barch/projects/chenaniah/web/chenaniah-web/logs/web-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Create bot service
    sudo tee /etc/systemd/system/chenaniah-bot.service << 'EOF'
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=barch
WorkingDirectory=/home/barch/chenaniah-bot
Environment=PATH=/home/barch/chenaniah-bot/venv/bin
ExecStart=/home/barch/chenaniah-bot/venv/bin/python telegram_bot_optimized.py

# Restart policy
Restart=always
RestartSec=10

# Performance settings
LimitNOFILE=65535
LimitNPROC=4096

# Logging
StandardOutput=append:/home/barch/chenaniah-bot/logs/bot.log
StandardError=append:/home/barch/chenaniah-bot/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    echo 'Systemd services created'
"

print_success "Systemd services created"
echo ""

# Step 10: Run system optimizations
print_status "Step 10: Running system optimizations..."

ssh $VPS_USER@$VPS_IP "
    echo 'Running system optimizations...'
    
    cd ~/chenaniah-bot
    
    # Run optimization script if it exists
    if [ -f optimize_vps.sh ]; then
        sudo bash optimize_vps.sh
    else
        echo 'Optimization script not found, applying basic optimizations...'
        
        # Basic optimizations
        sudo tee -a /etc/security/limits.conf << 'EOF'

# Increase file descriptor limits
* soft nofile 65535
* hard nofile 65535
barch soft nofile 65535
barch hard nofile 65535
EOF
        
        # Add swap if not exists
        if [ ! -f /swapfile ]; then
            sudo fallocate -l 4G /swapfile
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        fi
        
        # Optimize network
        sudo tee -a /etc/sysctl.conf << 'EOF'
net.core.somaxconn=4096
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_fastopen=3
EOF
        
        sudo sysctl -p
    fi
    
    echo 'System optimizations complete'
"

print_success "System optimizations complete"
echo ""

# Step 11: Setup environment variables
print_status "Step 11: Setting up environment variables..."

ssh $VPS_USER@$VPS_IP "
    echo 'Setting up environment variables...'
    
    cd ~/chenaniah-bot
    
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
    
    echo 'Environment variables template created'
"

print_warning "Environment variables template created - UPDATE REQUIRED!"
echo ""

# Step 12: Start services
print_status "Step 12: Starting services..."

ssh $VPS_USER@$VPS_IP "
    echo 'Starting services...'
    
    # Enable services
    sudo systemctl enable chenaniah-web
    sudo systemctl enable chenaniah-bot
    sudo systemctl enable nginx
    
    # Start nginx
    sudo systemctl start nginx
    
    # Start web application
    sudo systemctl start chenaniah-web
    
    # Wait for web to start
    sleep 5
    
    # Start bot (only if .env is configured)
    if grep -q 'your_bot_token_here' ~/chenaniah-bot/.env; then
        echo '⚠️  Bot not started - please update .env file first'
    else
        sudo systemctl start chenaniah-bot
        echo '✅ Bot started successfully'
    fi
    
    echo 'Services started'
"

print_success "Services started"
echo ""

# Step 13: Verify deployment
print_status "Step 13: Verifying deployment..."

ssh $VPS_USER@$VPS_IP "
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

# Step 14: Create management scripts
print_status "Step 14: Creating management scripts..."

ssh $VPS_USER@$VPS_IP "
    echo 'Creating management scripts...'
    
    cd ~/chenaniah-bot
    
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
    
    # Create update script
    cat > update-from-git.sh << 'EOF'
#!/bin/bash
echo 'Updating from git...'

# Update bot
cd ~/chenaniah-bot
if [ -d .git ]; then
    git pull origin main || git pull origin master
    source venv/bin/activate
    pip install -r requirements.txt
    sudo systemctl restart chenaniah-bot
    echo 'Bot updated'
else
    echo 'Bot not a git repository'
fi

# Update web
cd ~/projects/chenaniah/web/chenaniah-web
if [ -d .git ]; then
    git pull origin main || git pull origin master
    npm install
    npm run build
    sudo systemctl restart chenaniah-web
    echo 'Web updated'
else
    echo 'Web not a git repository'
fi

echo 'Update complete!'
EOF
    
    # Make scripts executable
    chmod +x *.sh
    
    echo 'Management scripts created:'
    echo '  - start-all.sh'
    echo '  - stop-all.sh'
    echo '  - restart-all.sh'
    echo '  - status-all.sh'
    echo '  - logs-all.sh'
    echo '  - update-from-git.sh'
"

print_success "Management scripts created"
echo ""

# Final summary
echo "======================================"
echo "🎉 GIT-BASED DEPLOYMENT COMPLETE!"
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
echo "   ./start-all.sh       # Start all services"
echo "   ./stop-all.sh        # Stop all services"
echo "   ./restart-all.sh     # Restart all services"
echo "   ./status-all.sh      # Check status"
echo "   ./logs-all.sh        # View logs"
echo "   ./update-from-git.sh # Update from git"
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
