#!/bin/bash

# Simple Deployment Script - No Interactive Sudo
# This script deploys both web and bot without interactive sudo prompts

echo "🚀 Simple Chenaniah Platform Deployment"
echo "======================================"
echo ""

# Configuration
VPS_IP="15.204.227.47"
VPS_USER="barch"

echo "Deploying to: $VPS_USER@$VPS_IP"
echo ""

# Check if we're in the right directory
if [ ! -f "telegram_bot_optimized.py" ]; then
    echo "❌ Error: Please run this script from the bot directory"
    echo "   Expected files: telegram_bot_optimized.py, database_optimized.py, etc."
    exit 1
fi

echo "✅ Found optimized bot files"
echo ""

# Step 1: Copy files to VPS
echo "📦 Step 1: Copying files to VPS..."

# Copy bot files
echo "   Copying bot files..."
scp -r . $VPS_USER@$VPS_IP:~/chenaniah-bot/

# Copy web files
echo "   Copying web files..."
scp -r ../web/chenaniah-web $VPS_USER@$VPS_IP:~/projects/chenaniah/web/

echo "✅ Files copied successfully"
echo ""

# Step 2: Deploy on VPS (non-interactive)
echo "🔧 Step 2: Deploying on VPS..."

ssh $VPS_USER@$VPS_IP '
    echo "Starting deployment on VPS..."
    
    # Update system (non-interactive)
    echo "Updating system packages..."
    sudo apt update -y
    sudo apt upgrade -y
    
    # Install required packages
    echo "Installing required packages..."
    sudo apt install -y python3 python3-pip python3-venv git nginx nodejs npm curl wget htop
    
    # Stop existing services
    echo "Stopping existing services..."
    sudo systemctl stop chenaniah-bot 2>/dev/null || echo "Bot service not running"
    sudo systemctl stop chenaniah-web 2>/dev/null || echo "Web service not running"
    sudo systemctl stop nginx 2>/dev/null || echo "Nginx not running"
    
    # Kill any running processes
    pkill -f telegram_bot.py 2>/dev/null || true
    pkill -f run_bot.py 2>/dev/null || true
    pkill -f node 2>/dev/null || true
    
    # Clean up old files
    echo "Cleaning up old files..."
    rm -rf ~/chenaniah-bot/*
    rm -rf ~/projects/chenaniah/web/*
    
    # Move files to correct locations
    echo "Setting up files..."
    mv ~/chenaniah-bot/* ~/chenaniah-bot/ 2>/dev/null || true
    mv ~/projects/chenaniah/web/chenaniah-web/* ~/projects/chenaniah/web/chenaniah-web/ 2>/dev/null || true
    
    # Setup bot
    echo "Setting up bot application..."
    cd ~/chenaniah-bot
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create directories
    mkdir -p logs data temp exports audio_files
    
    # Set permissions
    chmod +x *.sh *.py
    
    # Setup web
    echo "Setting up web application..."
    cd ~/projects/chenaniah/web/chenaniah-web
    npm install
    npm run build
    
    # Configure nginx
    echo "Configuring nginx..."
    sudo tee /etc/nginx/sites-available/chenaniah << "EOF"
server {
    listen 80;
    server_name 15.204.227.47;
    
    # Web application
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Audio files
    location /audio_files/ {
        alias /home/barch/chenaniah-bot/audio_files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Enable CORS for audio files
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/chenaniah /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx
    sudo nginx -t
    
    # Create services
    echo "Creating systemd services..."
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

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable chenaniah-web
    sudo systemctl enable chenaniah-bot
    sudo systemctl enable nginx
    
    # Start services
    sudo systemctl start nginx
    sudo systemctl start chenaniah-web
    
    # Wait for web to start
    sleep 5
    
    # Check if bot can start (only if .env is configured)
    if [ -f ~/chenaniah-bot/.env ] && ! grep -q "your_bot_token_here" ~/chenaniah-bot/.env; then
        sudo systemctl start chenaniah-bot
        echo "✅ Bot started"
    else
        echo "⚠️  Bot not started - please configure .env file"
    fi
    
    # Create management scripts
    cd ~/chenaniah-bot
    
    cat > start-all.sh << "EOF"
#!/bin/bash
echo "Starting all Chenaniah services..."
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot
echo "All services started!"
EOF
    
    cat > stop-all.sh << "EOF"
#!/bin/bash
echo "Stopping all Chenaniah services..."
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx
echo "All services stopped!"
EOF
    
    cat > restart-all.sh << "EOF"
#!/bin/bash
echo "Restarting all Chenaniah services..."
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot
echo "All services restarted!"
EOF
    
    cat > status-all.sh << "EOF"
#!/bin/bash
echo "=== Chenaniah Services Status ==="
echo ""
echo "Nginx:"
sudo systemctl status nginx --no-pager -l
echo ""
echo "Web App:"
sudo systemctl status chenaniah-web --no-pager -l
echo ""
echo "Bot:"
sudo systemctl status chenaniah-bot --no-pager -l
echo ""
echo "Ports:"
netstat -tlnp | grep -E ":(80|3000|5000)"
echo ""
echo "Resources:"
free -h
df -h
EOF
    
    cat > logs-all.sh << "EOF"
#!/bin/bash
echo "=== Chenaniah Services Logs ==="
echo ""
echo "Web App Logs:"
journalctl -u chenaniah-web -n 20 --no-pager
echo ""
echo "Bot Logs:"
journalctl -u chenaniah-bot -n 20 --no-pager
echo ""
echo "Nginx Logs:"
journalctl -u nginx -n 20 --no-pager
EOF
    
    # Make scripts executable
    chmod +x *.sh
    
    echo "✅ Deployment complete!"
'

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Web Application: http://$VPS_IP"
echo "🤖 Bot API: http://$VPS_IP/api/"
echo "🎵 Audio Files: http://$VPS_IP/audio_files/"
echo "❤️  Health Check: http://$VPS_IP/health"
echo ""
echo "📁 Directories:"
echo "   Web: /home/barch/projects/chenaniah/web/chenaniah-web"
echo "   Bot: /home/barch/chenaniah-bot"
echo ""
echo "🔧 Management Commands:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   cd ~/chenaniah-bot"
echo "   ./start-all.sh    # Start all services"
echo "   ./stop-all.sh     # Stop all services"
echo "   ./restart-all.sh  # Restart all services"
echo "   ./status-all.sh   # Check status"
echo "   ./logs-all.sh     # View logs"
echo ""
echo "⚠️  Next Steps:"
echo "1. Configure bot: ssh $VPS_USER@$VPS_IP"
echo "2. Edit ~/chenaniah-bot/.env with your bot token"
echo "3. Start bot: sudo systemctl start chenaniah-bot"
echo "4. Test: curl http://$VPS_IP/health"
echo ""
echo "🚀 Your platform is ready!"
