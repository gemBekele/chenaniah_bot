#!/bin/bash

# Fix Deployment Issues Script
# Run this on the VPS to fix the current issues

echo "🔧 Fixing Chenaniah Platform Issues"
echo "===================================="
echo ""

# Stop all services and processes
echo "🛑 Stopping all services and processes..."
sudo systemctl stop chenaniah-bot chenaniah-web nginx
pkill -f telegram_bot.py 2>/dev/null || true
pkill -f run_bot.py 2>/dev/null || true
pkill -f node 2>/dev/null || true
sleep 2

echo "✅ All services stopped"
echo ""

# Fix web application
echo "🌐 Fixing web application..."
cd ~/projects/chenaniah/web/chenaniah-web

# Check if package.json exists and has correct scripts
if [ -f package.json ]; then
    echo "📦 Checking package.json..."
    
    # Check if next is installed
    if ! npm list next >/dev/null 2>&1; then
        echo "📦 Installing Next.js..."
        npm install next@latest react@latest react-dom@latest
    fi
    
    # Check if build exists
    if [ ! -d ".next" ]; then
        echo "🏗️  Building web application..."
        npm run build
    fi
    
    # Update package.json scripts if needed
    echo "📝 Updating package.json scripts..."
    npm pkg set scripts.start="next start -p 3000"
    npm pkg set scripts.dev="next dev -p 3000"
    npm pkg set scripts.build="next build"
    
    echo "✅ Web application fixed"
else
    echo "❌ package.json not found in web directory"
    echo "   Current directory: $(pwd)"
    echo "   Contents:"
    ls -la
fi

echo ""

# Fix bot application
echo "🤖 Fixing bot application..."
cd ~/chenaniah-bot

# Check if optimized bot files exist
if [ -f telegram_bot_optimized.py ]; then
    echo "✅ Optimized bot files found"
else
    echo "❌ Optimized bot files not found"
    echo "   Available files:"
    ls -la *.py
fi

# Update systemd service to use correct bot file
echo "⚙️  Updating bot service..."
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
Restart=always
RestartSec=10
LimitNOFILE=65535

# Logging
StandardOutput=append:/home/barch/chenaniah-bot/logs/bot.log
StandardError=append:/home/barch/chenaniah-bot/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# Update web service
echo "⚙️  Updating web service..."
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

# Reload systemd
sudo systemctl daemon-reload

echo "✅ Services updated"
echo ""

# Fix nginx configuration
echo "⚙️  Fixing nginx configuration..."
sudo tee /etc/nginx/sites-available/chenaniah << 'EOF'
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
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

echo "✅ Nginx configuration updated"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p ~/projects/chenaniah/web/chenaniah-web/logs
mkdir -p ~/chenaniah-bot/logs
mkdir -p ~/chenaniah-bot/audio_files

echo "✅ Directories created"
echo ""

# Start services in order
echo "🚀 Starting services..."

# Start nginx first
sudo systemctl start nginx
sleep 2

# Start web application
sudo systemctl start chenaniah-web
sleep 5

# Check if web is running
if sudo systemctl is-active --quiet chenaniah-web; then
    echo "✅ Web application started"
else
    echo "❌ Web application failed to start"
    echo "   Checking logs..."
    journalctl -u chenaniah-web -n 10 --no-pager
fi

# Start bot
sudo systemctl start chenaniah-bot
sleep 2

# Check if bot is running
if sudo systemctl is-active --quiet chenaniah-bot; then
    echo "✅ Bot started"
else
    echo "❌ Bot failed to start"
    echo "   Checking logs..."
    journalctl -u chenaniah-bot -n 10 --no-pager
fi

echo ""

# Check final status
echo "📊 Final Status Check"
echo "===================="
echo ""

echo "Service Status:"
sudo systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"
sudo systemctl is-active chenaniah-web && echo "✅ Web App: Running" || echo "❌ Web App: Not running"
sudo systemctl is-active chenaniah-bot && echo "✅ Bot: Running" || echo "❌ Bot: Not running"

echo ""
echo "Port Status:"
netstat -tlnp 2>/dev/null | grep -E ':(80|3000|5000)' || echo "No services listening on expected ports"

echo ""
echo "Test Endpoints:"
curl -s -o /dev/null -w "Health Check: %{http_code}\n" http://localhost/health || echo "Health Check: Failed"
curl -s -o /dev/null -w "Web App: %{http_code}\n" http://localhost:3000 || echo "Web App: Failed"
curl -s -o /dev/null -w "Bot API: %{http_code}\n" http://localhost:5000/api/health || echo "Bot API: Failed"

echo ""
echo "======================================"
echo "🔧 Fix Complete!"
echo "======================================"
echo ""
echo "🌐 Access your platform at:"
echo "   http://15.204.227.47"
echo ""
echo "📋 If issues persist:"
echo "   ./logs.sh     - View logs"
echo "   ./status.sh   - Check status"
echo "   ./restart-all.sh - Restart services"
echo ""
