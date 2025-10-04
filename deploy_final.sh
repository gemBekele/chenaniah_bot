#!/bin/bash

# Final Deployment Script - Works with Sudo Password
# This script deploys both web and bot with proper sudo handling

echo "======================================"
echo "🚀 CHENANIAH PLATFORM DEPLOYMENT"
echo "======================================"
echo ""

# Configuration
VPS_IP="15.204.227.47"
VPS_USER="barch"

echo "This script will deploy to: $VPS_USER@$VPS_IP"
echo ""
echo "⚠️  You will be prompted for your sudo password on the VPS"
echo "   (This is normal and required for system configuration)"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Check if we're in the right directory
if [ ! -f "telegram_bot_optimized.py" ]; then
    echo "❌ Error: Please run this script from the bot directory"
    exit 1
fi

echo "✅ Found optimized bot files"
echo ""

# Step 1: Pull latest git changes locally
echo "📥 Step 1: Pulling latest changes from git..."
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "⚠️  No git remote or already up to date"
echo ""

# Step 2: Copy files to VPS
echo "📦 Step 2: Copying files to VPS..."
echo "   This may take a minute..."

# Create directories on VPS first
ssh $VPS_USER@$VPS_IP "mkdir -p ~/chenaniah-bot ~/projects/chenaniah/web"

# Copy bot files
echo "   Copying bot files..."
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    . $VPS_USER@$VPS_IP:~/chenaniah-bot/

# Copy web files
echo "   Copying web files..."
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '.git' \
    ../web/chenaniah-web/ $VPS_USER@$VPS_IP:~/projects/chenaniah/web/chenaniah-web/

echo "✅ Files copied successfully"
echo ""

# Step 3: Create deployment script on VPS
echo "🔧 Step 3: Creating deployment script on VPS..."

ssh $VPS_USER@$VPS_IP 'cat > ~/deploy_on_vps.sh << "DEPLOYEOF"
#!/bin/bash

echo "======================================"
echo "VPS Deployment Script"
echo "======================================"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv git nginx nodejs npm curl wget htop

# Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop chenaniah-bot 2>/dev/null || echo "Bot service not running"
sudo systemctl stop chenaniah-web 2>/dev/null || echo "Web service not running"

# Kill any running processes
pkill -f telegram_bot.py 2>/dev/null || true
pkill -f run_bot.py 2>/dev/null || true

# Setup bot application
echo "🤖 Setting up bot application..."
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
chmod +x *.sh 2>/dev/null || true

# Setup web application
echo "🌐 Setting up web application..."
cd ~/projects/chenaniah/web/chenaniah-web

# Install dependencies
npm install

# Build the application
npm run build

# Configure Nginx
echo "⚙️  Configuring Nginx..."
sudo tee /etc/nginx/sites-available/chenaniah << "EOF"
server {
    listen 80;
    server_name 15.204.227.47;
    
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
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Static files
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
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
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin *;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/chenaniah /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx
sudo nginx -t

# Create systemd services
echo "⚙️  Creating systemd services..."

sudo tee /etc/systemd/system/chenaniah-web.service << "EOF"
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

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/chenaniah-bot.service << "EOF"
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target

[Service]
Type=simple
User=barch
WorkingDirectory=/home/barch/chenaniah-bot
Environment=PATH=/home/barch/chenaniah-bot/venv/bin
ExecStart=/home/barch/chenaniah-bot/venv/bin/python telegram_bot_optimized.py
Restart=always
RestartSec=10
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable nginx
sudo systemctl enable chenaniah-web
sudo systemctl enable chenaniah-bot

# Start services
echo "🚀 Starting services..."
sudo systemctl start nginx
sudo systemctl start chenaniah-web

# Wait for web to start
sleep 5

# Check if bot is configured
if [ -f ~/chenaniah-bot/.env ] && ! grep -q "your_bot_token_here" ~/chenaniah-bot/.env; then
    sudo systemctl start chenaniah-bot
    echo "✅ Bot started"
else
    echo "⚠️  Bot not started - please configure .env file first"
fi

# Create management scripts
echo "📝 Creating management scripts..."
cd ~/chenaniah-bot

cat > start-all.sh << "MEOF"
#!/bin/bash
sudo systemctl start nginx chenaniah-web chenaniah-bot
echo "✅ All services started"
MEOF

cat > stop-all.sh << "MEOF"
#!/bin/bash
sudo systemctl stop chenaniah-bot chenaniah-web nginx
echo "✅ All services stopped"
MEOF

cat > restart-all.sh << "MEOF"
#!/bin/bash
sudo systemctl restart nginx chenaniah-web chenaniah-bot
echo "✅ All services restarted"
MEOF

cat > status.sh << "MEOF"
#!/bin/bash
echo "=== Service Status ==="
sudo systemctl status nginx --no-pager -l
echo ""
sudo systemctl status chenaniah-web --no-pager -l
echo ""
sudo systemctl status chenaniah-bot --no-pager -l
MEOF

cat > logs.sh << "MEOF"
#!/bin/bash
echo "=== Recent Logs ==="
echo ""
echo "Web App:"
journalctl -u chenaniah-web -n 20 --no-pager
echo ""
echo "Bot:"
journalctl -u chenaniah-bot -n 20 --no-pager
MEOF

cat > update.sh << "MEOF"
#!/bin/bash
echo "🔄 Updating from git..."
cd ~/chenaniah-bot
git pull origin main || git pull origin master
source venv/bin/activate
pip install -r requirements.txt
cd ~/projects/chenaniah/web/chenaniah-web
git pull origin main || git pull origin master
npm install
npm run build
echo "🚀 Restarting services..."
sudo systemctl restart chenaniah-bot chenaniah-web
echo "✅ Update complete"
MEOF

chmod +x *.sh

echo ""
echo "======================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🌐 Access Points:"
echo "   Web: http://15.204.227.47"
echo "   API: http://15.204.227.47/api/"
echo "   Audio: http://15.204.227.47/audio_files/"
echo "   Health: http://15.204.227.47/health"
echo ""
echo "🔧 Management Commands:"
echo "   ./start-all.sh   - Start all services"
echo "   ./stop-all.sh    - Stop all services"
echo "   ./restart-all.sh - Restart all services"
echo "   ./status.sh      - Check service status"
echo "   ./logs.sh        - View recent logs"
echo "   ./update.sh      - Update from git"
echo ""
echo "⚠️  Next Steps:"
echo "1. Edit ~/chenaniah-bot/.env with your bot token"
echo "2. Run: sudo systemctl start chenaniah-bot"
echo "3. Test: curl http://15.204.227.47/health"
echo ""
DEPLOYEOF

chmod +x ~/deploy_on_vps.sh
'

echo "✅ Deployment script created on VPS"
echo ""

# Step 4: Run deployment on VPS
echo "🚀 Step 4: Running deployment on VPS..."
echo ""
echo "⚠️  You will now be prompted for your sudo password"
echo "   (This is required to install packages and configure services)"
echo ""

ssh -t $VPS_USER@$VPS_IP "bash ~/deploy_on_vps.sh"

# Step 5: Verify deployment
echo ""
echo "✅ Step 5: Verifying deployment..."
echo ""

ssh $VPS_USER@$VPS_IP "
    echo '=== Service Status ==='
    sudo systemctl is-active nginx && echo '✅ Nginx: Running' || echo '❌ Nginx: Not running'
    sudo systemctl is-active chenaniah-web && echo '✅ Web App: Running' || echo '❌ Web App: Not running'
    sudo systemctl is-active chenaniah-bot && echo '✅ Bot: Running' || echo '⚠️  Bot: Not running (configure .env first)'
    echo ''
    echo '=== Port Status ==='
    netstat -tlnp 2>/dev/null | grep -E ':(80|3000|5000)' || echo 'Checking ports...'
"

echo ""
echo "======================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🌐 Your platform is now available at:"
echo "   http://$VPS_IP"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure your bot token:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   nano ~/chenaniah-bot/.env"
echo ""
echo "   Update these values:"
echo "   TELEGRAM_BOT_TOKEN=your_actual_bot_token"
echo "   API_SECRET_KEY=your_secure_secret_key"
echo "   ADMIN_PASSWORD=your_secure_password"
echo ""
echo "2. Start the bot:"
echo "   sudo systemctl start chenaniah-bot"
echo ""
echo "3. Test your deployment:"
echo "   curl http://$VPS_IP/health"
echo "   curl http://$VPS_IP/api/health"
echo ""
echo "4. Monitor services:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   cd ~/chenaniah-bot"
echo "   ./status.sh"
echo "   ./logs.sh"
echo ""
echo "🚀 Your Chenaniah platform is ready!"
echo "======================================"
