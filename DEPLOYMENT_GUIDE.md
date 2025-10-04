# 🚀 Complete Deployment Guide

## Fresh VPS Deployment - Web + Bot

This guide will help you deploy both the Chenaniah web application and the optimized bot to your VPS.

---

## 📋 Prerequisites

- VPS IP: `15.204.227.47`
- SSH access as user `barch`
- Bot token from Telegram BotFather
- Both web and bot code ready

---

## 🎯 Quick Deployment (Recommended)

### Option 1: Simple Deploy Script

```bash
# From your local machine, in the bot directory
cd /home/barch/projects/chenaniah/bot

# Run the deployment script
./deploy.sh
```

This script will:
- ✅ Copy all files to VPS
- ✅ Install dependencies
- ✅ Configure Nginx
- ✅ Create systemd services
- ✅ Start all services
- ✅ Set up management commands

---

## 🔧 Manual Deployment (Step by Step)

### Step 1: Prepare Files

```bash
# Make sure you're in the bot directory
cd /home/barch/projects/chenaniah/bot

# Verify optimized files exist
ls -la telegram_bot_optimized.py database_optimized.py submission_queue.py performance_monitor.py
```

### Step 2: Copy Files to VPS

```bash
# Copy bot files
scp -r . barch@15.204.227.47:~/chenaniah-bot/

# Copy web files
scp -r ../web/chenaniah-web barch@15.204.227.47:~/projects/chenaniah/web/
```

### Step 3: Connect to VPS and Deploy

```bash
# Connect to VPS
ssh barch@15.204.227.47

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git nginx nodejs npm curl wget htop

# Stop any existing services
sudo systemctl stop chenaniah-bot 2>/dev/null || true
sudo systemctl stop chenaniah-web 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true
```

### Step 4: Setup Bot Application

```bash
# Go to bot directory
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
```

### Step 5: Setup Web Application

```bash
# Go to web directory
cd ~/projects/chenaniah/web/chenaniah-web

# Install dependencies
npm install

# Build the application
npm run build
```

### Step 6: Configure Nginx

```bash
# Create nginx configuration
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
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
```

### Step 7: Create Systemd Services

```bash
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
```

### Step 8: Run System Optimizations

```bash
# Go to bot directory
cd ~/chenaniah-bot

# Run optimization script
sudo bash optimize_vps.sh
```

### Step 9: Configure Environment Variables

```bash
# Create .env file for bot
cd ~/chenaniah-bot

cat > .env << 'EOF'
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database
DATABASE_PATH=./vocalist_screening.db

# Server
BASE_URL=http://15.204.227.47
PORT=5000

# API
API_SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF

echo "⚠️  IMPORTANT: Update .env file with your actual values!"
echo "   - TELEGRAM_BOT_TOKEN"
echo "   - API_SECRET_KEY"
echo "   - ADMIN_PASSWORD"
```

### Step 10: Start Services

```bash
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
```

### Step 11: Verify Deployment

```bash
# Check service status
sudo systemctl status chenaniah-web
sudo systemctl status chenaniah-bot
sudo systemctl status nginx

# Check ports
netstat -tlnp | grep -E ':(80|3000|5000)'

# Test endpoints
curl http://15.204.227.47/health
curl http://15.204.227.47/api/health
```

---

## 🎮 Management Commands

### Service Management

```bash
# Start all services
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot

# Stop all services
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx

# Restart all services
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot

# Check status
sudo systemctl status chenaniah-web
sudo systemctl status chenaniah-bot
sudo systemctl status nginx
```

### Log Monitoring

```bash
# View logs in real-time
journalctl -u chenaniah-web -f
journalctl -u chenaniah-bot -f
journalctl -u nginx -f

# View recent logs
journalctl -u chenaniah-web -n 50
journalctl -u chenaniah-bot -n 50
journalctl -u nginx -n 50

# View error logs only
journalctl -u chenaniah-web -p err
journalctl -u chenaniah-bot -p err
journalctl -u nginx -p err
```

### Quick Management Scripts

```bash
# Create management scripts
cd ~/chenaniah-bot

# Start all script
cat > start-all.sh << 'EOF'
#!/bin/bash
echo 'Starting all Chenaniah services...'
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot
echo 'All services started!'
EOF

# Stop all script
cat > stop-all.sh << 'EOF'
#!/bin/bash
echo 'Stopping all Chenaniah services...'
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx
echo 'All services stopped!'
EOF

# Restart all script
cat > restart-all.sh << 'EOF'
#!/bin/bash
echo 'Restarting all Chenaniah services...'
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot
echo 'All services restarted!'
EOF

# Status script
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

# Make scripts executable
chmod +x *.sh
```

---

## 🌐 Access Points

After deployment, your platform will be available at:

- **Web Application**: http://15.204.227.47
- **Bot API**: http://15.204.227.47/api/
- **Audio Files**: http://15.204.227.47/audio_files/
- **Health Check**: http://15.204.227.47/health
- **Bot Health**: http://15.204.227.47/api/health

---

## 🔧 Configuration

### Bot Configuration (.env)

```bash
# Edit bot configuration
nano ~/chenaniah-bot/.env

# Required values:
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
API_SECRET_KEY=your-super-secret-key-here
ADMIN_PASSWORD=your-secure-admin-password
```

### Web Configuration

```bash
# Edit web configuration if needed
nano ~/projects/chenaniah/web/chenaniah-web/.env.local

# Common settings:
NEXT_PUBLIC_API_URL=http://15.204.227.47/api
NEXT_PUBLIC_BASE_URL=http://15.204.227.47
```

---

## 🚨 Troubleshooting

### Common Issues

#### Bot not starting
```bash
# Check logs
journalctl -u chenaniah-bot -n 50

# Check if .env is configured
cat ~/chenaniah-bot/.env

# Check if token is valid
grep TELEGRAM_BOT_TOKEN ~/chenaniah-bot/.env
```

#### Web app not loading
```bash
# Check logs
journalctl -u chenaniah-web -n 50

# Check if port 3000 is listening
netstat -tlnp | grep :3000

# Restart web service
sudo systemctl restart chenaniah-web
```

#### Nginx errors
```bash
# Test configuration
sudo nginx -t

# Check logs
journalctl -u nginx -n 50

# Restart nginx
sudo systemctl restart nginx
```

#### Port conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E ':(80|3000|5000)'

# Kill conflicting processes
sudo pkill -f node
sudo pkill -f python
```

---

## 📊 Monitoring

### System Resources

```bash
# Check system resources
free -h
df -h
top -bn1 | head -20

# Check specific processes
ps aux | grep -E "(node|python|nginx)"
```

### Application Health

```bash
# Test web app
curl -I http://15.204.227.47

# Test bot API
curl -I http://15.204.227.47/api/health

# Test audio serving
curl -I http://15.204.227.47/audio_files/
```

### Bot Statistics

Use the `/stats` command in your Telegram bot to see:
- Queue status
- Database statistics
- System performance
- Processing metrics

---

## 🔄 Updates and Maintenance

### Updating Bot

```bash
# Copy new files
scp -r . barch@15.204.227.47:~/chenaniah-bot/

# On VPS
ssh barch@15.204.227.47
cd ~/chenaniah-bot
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chenaniah-bot
```

### Updating Web App

```bash
# Copy new files
scp -r ../web/chenaniah-web barch@15.204.227.47:~/projects/chenaniah/web/

# On VPS
ssh barch@15.204.227.47
cd ~/projects/chenaniah/web/chenaniah-web
npm install
npm run build
sudo systemctl restart chenaniah-web
```

### Database Maintenance

```bash
# Backup database
cp ~/chenaniah-bot/vocalist_screening.db ~/vocalist_screening.db.backup

# Optimize database
cd ~/chenaniah-bot
sqlite3 vocalist_screening.db "PRAGMA optimize;"
sqlite3 vocalist_screening.db "VACUUM;"
```

---

## ✅ Deployment Checklist

- [ ] VPS accessible via SSH
- [ ] Bot token obtained from BotFather
- [ ] All optimized files copied to VPS
- [ ] Dependencies installed
- [ ] Nginx configured
- [ ] Systemd services created
- [ ] System optimizations applied
- [ ] Environment variables configured
- [ ] Services started
- [ ] Health checks passing
- [ ] Bot responding to /start command
- [ ] Web app loading correctly
- [ ] Audio files accessible

---

## 🎉 Success!

Your Chenaniah platform is now deployed and ready for launch!

**Access URLs:**
- Web: http://15.204.227.47
- Bot API: http://15.204.227.47/api/
- Audio: http://15.204.227.47/audio_files/

**Management:**
- SSH: `ssh barch@15.204.227.47`
- Services: `sudo systemctl status chenaniah-*`
- Logs: `journalctl -u chenaniah-* -f`

**Next Steps:**
1. Test all functionality
2. Configure SSL certificate (optional)
3. Set up monitoring alerts
4. Plan for scaling if needed

🚀 **Ready for launch!**