#!/bin/bash

# Quick New VPS Deployment Script
# This script deploys Chenaniah platform to a completely new VPS

set -e

echo "🚀 Chenaniah Platform - New VPS Deployment"
echo "=========================================="
echo ""

# Configuration - UPDATE THESE VALUES
VPS_IP="YOUR_VPS_IP_HERE"
VPS_USER="root"  # or your username
VPS_USERNAME="barch"  # username to create/use

echo "⚠️  IMPORTANT: Update the VPS_IP and VPS_USER variables in this script first!"
echo ""
echo "Current configuration:"
echo "  VPS IP: $VPS_IP"
echo "  VPS User: $VPS_USER"
echo "  Target Username: $VPS_USERNAME"
echo ""

if [ "$VPS_IP" = "YOUR_VPS_IP_HERE" ]; then
    echo "❌ Please update VPS_IP in the script first!"
    exit 1
fi

read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Check if we're in the right directory
if [ ! -f "telegram_bot_optimized.py" ]; then
    echo "❌ Error: Please run this script from the bot directory"
    exit 1
fi

echo "✅ Found optimized bot files"
echo ""

# Step 1: Prepare VPS
echo "🔧 Step 1: Preparing VPS environment..."
ssh $VPS_USER@$VPS_IP "
    echo 'Updating system...'
    apt update && apt upgrade -y
    
    echo 'Installing required packages...'
    apt install -y curl wget git htop nano ufw python3 python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev nginx nodejs npm certbot python3-certbot-nginx fail2ban
    
    echo 'Creating user account...'
    if ! id '$VPS_USERNAME' &>/dev/null; then
        adduser --disabled-password --gecos '' '$VPS_USERNAME'
        usermod -aG sudo '$VPS_USERNAME'
    fi
    
    echo 'Creating project directories...'
    mkdir -p /home/$VPS_USERNAME/projects/chenaniah/web
    mkdir -p /home/$VPS_USERNAME/chenaniah-bot/{logs,data,temp,exports,audio_files}
    mkdir -p /home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web/logs
    
    echo 'Setting permissions...'
    chown -R $VPS_USERNAME:$VPS_USERNAME /home/$VPS_USERNAME/projects
    chown -R $VPS_USERNAME:$VPS_USERNAME /home/$VPS_USERNAME/chenaniah-bot
"

echo "✅ VPS environment prepared"
echo ""

# Step 2: Copy files
echo "📦 Step 2: Copying application files..."

# Copy bot files
echo "   Copying bot files..."
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
    . $VPS_USER@$VPS_IP:/home/$VPS_USERNAME/chenaniah-bot/

# Copy web files
echo "   Copying web files..."
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '.git' \
    ../web/chenaniah-web/ $VPS_USER@$VPS_IP:/home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web/

echo "✅ Files copied successfully"
echo ""

# Step 3: Deploy on VPS
echo "🚀 Step 3: Deploying applications on VPS..."

ssh $VPS_USER@$VPS_IP "
    echo 'Setting up bot application...'
    cd /home/$VPS_USERNAME/chenaniah-bot
    
    # Create virtual environment
    sudo -u $VPS_USERNAME python3 -m venv venv
    sudo -u $VPS_USERNAME bash -c 'source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'
    
    # Set permissions
    chown -R $VPS_USERNAME:$VPS_USERNAME venv
    chmod +x *.sh *.py
    
    echo 'Setting up web application...'
    cd /home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web
    
    # Install dependencies and build
    sudo -u $VPS_USERNAME npm install
    sudo -u $VPS_USERNAME npm run build
    
    echo 'Configuring Nginx...'
    # Create nginx configuration
    cat > /etc/nginx/sites-available/chenaniah << 'EOF'
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
        proxy_set_header Connection \"upgrade\";
        proxy_cache_bypass \$http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control \"public, immutable\";
    }
    
    # Bot API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Audio files
    location /audio_files/ {
        alias /home/$VPS_USERNAME/chenaniah-bot/audio_files/;
        expires 1y;
        add_header Cache-Control \"public, immutable\";
        add_header Access-Control-Allow-Origin *;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 \"healthy\\n\";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/chenaniah /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx
    nginx -t
    
    echo 'Creating systemd services...'
    # Create web service
    cat > /etc/systemd/system/chenaniah-web.service << 'EOF'
[Unit]
Description=Chenaniah Web Application
After=network.target

[Service]
Type=simple
User=$VPS_USERNAME
WorkingDirectory=/home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web/logs/web.log
StandardError=append:/home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web/logs/web-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Create bot service
    cat > /etc/systemd/system/chenaniah-bot.service << 'EOF'
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$VPS_USERNAME
WorkingDirectory=/home/$VPS_USERNAME/chenaniah-bot
Environment=PATH=/home/$VPS_USERNAME/chenaniah-bot/venv/bin
ExecStart=/home/$VPS_USERNAME/chenaniah-bot/venv/bin/python telegram_bot_optimized.py
Restart=always
RestartSec=10

# Performance settings
LimitNOFILE=65535
LimitNPROC=4096

# Logging
StandardOutput=append:/home/$VPS_USERNAME/chenaniah-bot/logs/bot.log
StandardError=append:/home/$VPS_USERNAME/chenaniah-bot/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable nginx
    systemctl enable chenaniah-web
    systemctl enable chenaniah-bot
    
    echo 'Starting services...'
    # Start services
    systemctl start nginx
    systemctl start chenaniah-web
    
    # Wait for web to start
    sleep 5
    
    # Check if web is running before starting bot
    if systemctl is-active --quiet chenaniah-web; then
        echo 'Web app started successfully'
        # Create .env file template
        sudo -u $VPS_USERNAME cat > /home/$VPS_USERNAME/chenaniah-bot/.env << 'ENVEOF'
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
ENVEOF
        
        echo '⚠️  Bot not started - please configure .env file first'
    else
        echo '❌ Web app failed to start'
    fi
    
    echo 'Creating management scripts...'
    cd /home/$VPS_USERNAME/chenaniah-bot
    
    # Create management scripts
    sudo -u $VPS_USERNAME cat > start-all.sh << 'SCRIPTEOF'
#!/bin/bash
echo \"🚀 Starting all Chenaniah services...\"
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot
echo \"✅ All services started!\"
SCRIPTEOF
    
    sudo -u $VPS_USERNAME cat > stop-all.sh << 'SCRIPTEOF'
#!/bin/bash
echo \"🛑 Stopping all Chenaniah services...\"
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx
echo \"✅ All services stopped!\"
SCRIPTEOF
    
    sudo -u $VPS_USERNAME cat > restart-all.sh << 'SCRIPTEOF'
#!/bin/bash
echo \"🔄 Restarting all Chenaniah services...\"
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot
echo \"✅ All services restarted!\"
SCRIPTEOF
    
    sudo -u $VPS_USERNAME cat > status.sh << 'SCRIPTEOF'
#!/bin/bash
echo \"📊 Chenaniah Services Status\"
echo \"==========================\"
echo \"\"
echo \"Nginx:\"
sudo systemctl status nginx --no-pager -l
echo \"\"
echo \"Web App:\"
sudo systemctl status chenaniah-web --no-pager -l
echo \"\"
echo \"Bot:\"
sudo systemctl status chenaniah-bot --no-pager -l
echo \"\"
echo \"Ports:\"
netstat -tlnp | grep -E ':(80|3000|5000)'
echo \"\"
echo \"Resources:\"
free -h
df -h
SCRIPTEOF
    
    sudo -u $VPS_USERNAME cat > logs.sh << 'SCRIPTEOF'
#!/bin/bash
echo \"📋 Chenaniah Services Logs\"
echo \"=========================\"
echo \"\"
echo \"Web App Logs:\"
journalctl -u chenaniah-web -n 20 --no-pager
echo \"\"
echo \"Bot Logs:\"
journalctl -u chenaniah-bot -n 20 --no-pager
echo \"\"
echo \"Nginx Logs:\"
journalctl -u nginx -n 20 --no-pager
SCRIPTEOF
    
    # Make scripts executable
    chmod +x *.sh
    chown $VPS_USERNAME:$VPS_USERNAME *.sh
    
    echo '✅ Deployment complete!'
"

echo "✅ Deployment completed successfully!"
echo ""

# Step 4: Final verification
echo "🔍 Step 4: Verifying deployment..."
ssh $VPS_USER@$VPS_IP "
    echo '=== Service Status ==='
    systemctl is-active nginx && echo '✅ Nginx: Running' || echo '❌ Nginx: Not running'
    systemctl is-active chenaniah-web && echo '✅ Web App: Running' || echo '❌ Web App: Not running'
    systemctl is-active chenaniah-bot && echo '✅ Bot: Running' || echo '⚠️  Bot: Not running (configure .env first)'
    echo ''
    echo '=== Port Status ==='
    netstat -tlnp | grep -E ':(80|3000|5000)' || echo 'Checking ports...'
    echo ''
    echo '=== Test Endpoints ==='
    curl -s -o /dev/null -w 'Health Check: %{http_code}' http://localhost/health && echo '' || echo 'Health Check: Failed'
    curl -s -o /dev/null -w 'Web App: %{http_code}' http://localhost:3000 && echo '' || echo 'Web App: Failed'
"

echo ""
echo "======================================"
echo "🎉 NEW VPS DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🌐 Your platform is now available at:"
echo "   http://$VPS_IP"
echo ""
echo "📁 Directories:"
echo "   Web: /home/$VPS_USERNAME/projects/chenaniah/web/chenaniah-web"
echo "   Bot: /home/$VPS_USERNAME/chenaniah-bot"
echo ""
echo "🔧 Management Commands:"
echo "   ssh $VPS_USERNAME@$VPS_IP"
echo "   cd ~/chenaniah-bot"
echo "   ./start-all.sh    # Start all services"
echo "   ./stop-all.sh     # Stop all services"
echo "   ./restart-all.sh  # Restart all services"
echo "   ./status.sh       # Check status"
echo "   ./logs.sh         # View logs"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Configure bot token:"
echo "   ssh $VPS_USERNAME@$VPS_IP"
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
echo "3. Test the deployment:"
echo "   curl http://$VPS_IP/health"
echo "   curl http://$VPS_IP/api/health"
echo ""
echo "4. Configure security (optional):"
echo "   sudo ufw enable"
echo "   sudo ufw allow ssh"
echo "   sudo ufw allow 80"
echo "   sudo ufw allow 443"
echo ""
echo "🚀 Your Chenaniah platform is ready!"
echo "======================================"
