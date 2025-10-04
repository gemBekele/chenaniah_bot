# 🚀 Complete New VPS Deployment Guide

## Step-by-Step Guide to Deploy Chenaniah Platform on a Fresh VPS

This guide will help you deploy both the web application and optimized bot on a completely new VPS.

---

## 📋 Prerequisites

- **New VPS** with Ubuntu 20.04+ or similar
- **SSH access** to the VPS
- **Domain/IP address** of your VPS
- **Telegram Bot Token** from BotFather
- **Local machine** with your code ready

---

## 🎯 Step 1: Prepare Your Local Machine

### 1.1 Ensure You Have All Files
```bash
# Navigate to your project directory
cd /home/barch/projects/chenaniah/bot

# Verify you have the optimized files
ls -la telegram_bot_optimized.py database_optimized.py submission_queue.py performance_monitor.py

# Verify web files exist
ls -la ../web/chenaniah-web/
```

### 1.2 Fix TypeScript Error (if not done already)
```bash
# Fix the admin dashboard TypeScript error
cd ../web/chenaniah-web
sed -i 's/submission\.audio_file_path || submission\.audio_drive_link || '\'''\''/submission.audio_file_path || '\'''\''/g' components/admin-dashboard.tsx
sed -i 's/!submission\.audio_file_path && !submission\.audio_drive_link/!submission.audio_file_path/g' components/admin-dashboard.tsx
```

---

## 🖥️ Step 2: Set Up Your New VPS

### 2.1 Connect to Your VPS
```bash
# Replace YOUR_VPS_IP with your actual VPS IP
ssh root@YOUR_VPS_IP
# OR if using a user account:
# ssh username@YOUR_VPS_IP
```

### 2.2 Update System
```bash
# Update package lists
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git htop nano ufw
```

### 2.3 Create User Account (if using root)
```bash
# Create a user account (replace 'barch' with your preferred username)
adduser barch
usermod -aG sudo barch

# Switch to the new user
su - barch
```

### 2.4 Configure SSH (Optional but Recommended)
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Uncomment and set:
# PermitRootLogin no
# PasswordAuthentication no (if using SSH keys)

# Restart SSH
sudo systemctl restart ssh
```

---

## 🔧 Step 3: Install Required Software

### 3.1 Install Node.js and NPM
```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### 3.2 Install Python and Dependencies
```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install additional packages
sudo apt install -y build-essential libssl-dev libffi-dev
```

### 3.3 Install Nginx
```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### 3.4 Install Additional Tools
```bash
# Install additional useful packages
sudo apt install -y certbot python3-certbot-nginx ufw fail2ban
```

---

## 📁 Step 4: Create Project Directories

### 4.1 Create Directory Structure
```bash
# Create main project directory
mkdir -p ~/projects/chenaniah/web
mkdir -p ~/chenaniah-bot

# Create subdirectories
mkdir -p ~/chenaniah-bot/{logs,data,temp,exports,audio_files}
mkdir -p ~/projects/chenaniah/web/chenaniah-web/logs
```

### 4.2 Set Permissions
```bash
# Set proper permissions
chmod 755 ~/projects/chenaniah
chmod 755 ~/chenaniah-bot
```

---

## 📦 Step 5: Deploy Application Files

### 5.1 Copy Files from Local Machine

**From your local machine, run:**
```bash
# Copy bot files
scp -r /home/barch/projects/chenaniah/bot/* username@YOUR_VPS_IP:~/chenaniah-bot/

# Copy web files
scp -r /home/barch/projects/chenaniah/web/chenaniah-web/* username@YOUR_VPS_IP:~/projects/chenaniah/web/chenaniah-web/
```

**Or use rsync for better efficiency:**
```bash
# Copy bot files
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
    /home/barch/projects/chenaniah/bot/ username@YOUR_VPS_IP:~/chenaniah-bot/

# Copy web files
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '.git' \
    /home/barch/projects/chenaniah/web/chenaniah-web/ username@YOUR_VPS_IP:~/projects/chenaniah/web/chenaniah-web/
```

### 5.2 Verify Files on VPS
```bash
# Check bot files
ls -la ~/chenaniah-bot/

# Check web files
ls -la ~/projects/chenaniah/web/chenaniah-web/
```

---

## 🐍 Step 6: Set Up Bot Application

### 6.1 Create Python Virtual Environment
```bash
# Navigate to bot directory
cd ~/chenaniah-bot

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 6.2 Install Python Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### 6.3 Configure Environment Variables
```bash
# Create .env file
nano .env
```

**Add the following content (replace with your actual values):**
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here

# Database
DATABASE_PATH=./vocalist_screening.db

# Server
BASE_URL=http://YOUR_VPS_IP
PORT=5000

# API
API_SECRET_KEY=your-super-secret-key-change-this
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# Optional: Google Drive (if using)
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_SHEET_ID=your_sheet_id_here
```

### 6.4 Test Bot Installation
```bash
# Test bot (this will run in foreground - press Ctrl+C to stop)
python telegram_bot_optimized.py
```

---

## 🌐 Step 7: Set Up Web Application

### 7.1 Install Node.js Dependencies
```bash
# Navigate to web directory
cd ~/projects/chenaniah/web/chenaniah-web

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

### 7.2 Build Web Application
```bash
# Build the application
npm run build

# Verify build
ls -la .next/
```

### 7.3 Test Web Application
```bash
# Test web app (this will run in foreground - press Ctrl+C to stop)
npm start
```

---

## ⚙️ Step 8: Configure Nginx

### 8.1 Create Nginx Configuration
```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/chenaniah
```

**Add the following configuration (replace YOUR_VPS_IP with your actual IP):**
```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;
    
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
```

### 8.2 Enable Site
```bash
# Enable the site
sudo ln -sf /etc/nginx/sites-available/chenaniah /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## 🔄 Step 9: Create Systemd Services

### 9.1 Create Web Service
```bash
# Create web service
sudo nano /etc/systemd/system/chenaniah-web.service
```

**Add the following content:**
```ini
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
```

### 9.2 Create Bot Service
```bash
# Create bot service
sudo nano /etc/systemd/system/chenaniah-bot.service
```

**Add the following content:**
```ini
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

# Performance settings
LimitNOFILE=65535
LimitNPROC=4096

# Logging
StandardOutput=append:/home/barch/chenaniah-bot/logs/bot.log
StandardError=append:/home/barch/chenaniah-bot/logs/bot-error.log

[Install]
WantedBy=multi-user.target
```

### 9.3 Reload and Enable Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable chenaniah-web
sudo systemctl enable chenaniah-bot
sudo systemctl enable nginx
```

---

## 🚀 Step 10: Start Services

### 10.1 Start Services in Order
```bash
# Start nginx first
sudo systemctl start nginx

# Start web application
sudo systemctl start chenaniah-web

# Wait for web to start
sleep 5

# Start bot
sudo systemctl start chenaniah-bot
```

### 10.2 Check Service Status
```bash
# Check all services
sudo systemctl status nginx
sudo systemctl status chenaniah-web
sudo systemctl status chenaniah-bot

# Check if ports are listening
netstat -tlnp | grep -E ':(80|3000|5000)'
```

---

## 🔧 Step 11: System Optimizations

### 11.1 Run System Optimizations
```bash
# Navigate to bot directory
cd ~/chenaniah-bot

# Run optimization script (if available)
sudo bash optimize_vps.sh
```

### 11.2 Manual Optimizations
```bash
# Increase file descriptor limits
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "barch soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "barch hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize network settings
echo 'net.core.somaxconn=4096' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max=16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max=16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 📝 Step 12: Create Management Scripts

### 12.1 Create Management Scripts
```bash
# Navigate to bot directory
cd ~/chenaniah-bot

# Create start script
cat > start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting all Chenaniah services..."
sudo systemctl start nginx
sudo systemctl start chenaniah-web
sudo systemctl start chenaniah-bot
echo "✅ All services started!"
EOF

# Create stop script
cat > stop-all.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping all Chenaniah services..."
sudo systemctl stop chenaniah-bot
sudo systemctl stop chenaniah-web
sudo systemctl stop nginx
echo "✅ All services stopped!"
EOF

# Create restart script
cat > restart-all.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting all Chenaniah services..."
sudo systemctl restart nginx
sudo systemctl restart chenaniah-web
sudo systemctl restart chenaniah-bot
echo "✅ All services restarted!"
EOF

# Create status script
cat > status.sh << 'EOF'
#!/bin/bash
echo "📊 Chenaniah Services Status"
echo "=========================="
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
netstat -tlnp | grep -E ':(80|3000|5000)'
echo ""
echo "Resources:"
free -h
df -h
EOF

# Create logs script
cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Chenaniah Services Logs"
echo "========================="
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
```

---

## 🧪 Step 13: Test Deployment

### 13.1 Test All Endpoints
```bash
# Test health check
curl http://YOUR_VPS_IP/health

# Test web application
curl http://YOUR_VPS_IP/

# Test bot API
curl http://YOUR_VPS_IP/api/health

# Test audio files directory
curl http://YOUR_VPS_IP/audio_files/
```

### 13.2 Test Bot in Telegram
1. Open Telegram
2. Find your bot
3. Send `/start` command
4. Verify bot responds correctly

### 13.3 Test Web Interface
1. Open browser
2. Go to `http://YOUR_VPS_IP`
3. Verify web application loads
4. Test admin login (if applicable)

---

## 🔒 Step 14: Security Configuration

### 14.1 Configure Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

### 14.2 Configure Fail2Ban
```bash
# Configure fail2ban for SSH
sudo nano /etc/fail2ban/jail.local
```

**Add the following content:**
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
```

```bash
# Start fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## 📊 Step 15: Monitoring Setup

### 15.1 Create Monitoring Script
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "🔍 Chenaniah Platform Monitoring"
echo "==============================="
echo ""
echo "Service Status:"
sudo systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"
sudo systemctl is-active chenaniah-web && echo "✅ Web App: Running" || echo "❌ Web App: Not running"
sudo systemctl is-active chenaniah-bot && echo "✅ Bot: Running" || echo "❌ Bot: Not running"
echo ""
echo "System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
echo ""
echo "Network Connections:"
netstat -tlnp | grep -E ':(80|3000|5000)' | wc -l | xargs echo "Active connections:"
EOF

chmod +x monitor.sh
```

### 15.2 Set Up Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/chenaniah
```

**Add the following content:**
```
/home/barch/chenaniah-bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 barch barch
    sharedscripts
    postrotate
        systemctl reload chenaniah-bot > /dev/null 2>&1 || true
    endscript
}

/home/barch/projects/chenaniah/web/chenaniah-web/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 barch barch
    sharedscripts
    postrotate
        systemctl reload chenaniah-web > /dev/null 2>&1 || true
    endscript
}
```

---

## 🎉 Step 16: Final Verification

### 16.1 Complete System Check
```bash
# Run complete check
./status.sh
./monitor.sh
./logs.sh
```

### 16.2 Performance Test
```bash
# Test with multiple requests
for i in {1..10}; do
    curl -s -o /dev/null -w "Request $i: %{http_code}\n" http://YOUR_VPS_IP/health
done
```

---

## 📋 Step 17: Backup and Maintenance

### 17.1 Create Backup Script
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/barch/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp ~/chenaniah-bot/vocalist_screening.db $BACKUP_DIR/vocalist_screening_$DATE.db

# Backup audio files
tar -czf $BACKUP_DIR/audio_files_$DATE.tar.gz ~/chenaniah-bot/audio_files/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz ~/chenaniah-bot/.env /etc/nginx/sites-available/chenaniah /etc/systemd/system/chenaniah-*.service

echo "✅ Backup completed: $BACKUP_DIR"
EOF

chmod +x backup.sh
```

### 17.2 Set Up Automated Backups
```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/barch/chenaniah-bot/backup.sh") | crontab -
```

---

## 🎯 Final Checklist

- [ ] ✅ VPS set up and updated
- [ ] ✅ All software installed (Node.js, Python, Nginx)
- [ ] ✅ Project files copied to VPS
- [ ] ✅ Bot environment configured (.env file)
- [ ] ✅ Web application built successfully
- [ ] ✅ Nginx configured and tested
- [ ] ✅ Systemd services created and enabled
- [ ] ✅ All services running
- [ ] ✅ System optimizations applied
- [ ] ✅ Management scripts created
- [ ] ✅ Security configured (firewall, fail2ban)
- [ ] ✅ Monitoring set up
- [ ] ✅ Backup system configured
- [ ] ✅ Platform accessible via web browser
- [ ] ✅ Bot responding in Telegram
- [ ] ✅ All endpoints tested

---

## 🌐 Access Your Platform

After successful deployment, your platform will be available at:

- **Web Application**: `http://YOUR_VPS_IP`
- **Bot API**: `http://YOUR_VPS_IP/api/`
- **Audio Files**: `http://YOUR_VPS_IP/audio_files/`
- **Health Check**: `http://YOUR_VPS_IP/health`

---

## 🔧 Management Commands

```bash
# Service management
./start-all.sh    # Start all services
./stop-all.sh     # Stop all services
./restart-all.sh  # Restart all services
./status.sh       # Check service status
./logs.sh         # View recent logs
./monitor.sh      # System monitoring
./backup.sh       # Create backup
```

---

## 🆘 Troubleshooting

### Common Issues:

1. **502 Bad Gateway**: Check if web app is running on port 3000
2. **Bot not responding**: Check bot token in .env file
3. **Services not starting**: Check logs with `journalctl -u service-name`
4. **Permission errors**: Ensure user has proper permissions
5. **Port conflicts**: Check what's using ports 80, 3000, 5000

### Useful Commands:

```bash
# Check service logs
journalctl -u chenaniah-web -f
journalctl -u chenaniah-bot -f
journalctl -u nginx -f

# Check port usage
netstat -tlnp | grep -E ':(80|3000|5000)'

# Check system resources
htop
free -h
df -h

# Test endpoints
curl http://YOUR_VPS_IP/health
curl http://YOUR_VPS_IP/api/health
```

---

## 🎉 Congratulations!

Your Chenaniah platform is now successfully deployed on your new VPS! 

The platform includes:
- ✅ **Optimized Telegram Bot** with queue system and rate limiting
- ✅ **Next.js Web Application** with admin dashboard
- ✅ **Nginx Reverse Proxy** for optimal performance
- ✅ **Systemd Services** for automatic restart
- ✅ **Performance Monitoring** and logging
- ✅ **Security Configuration** with firewall and fail2ban
- ✅ **Backup System** for data protection
- ✅ **Management Scripts** for easy maintenance

**Your platform is ready for production use!** 🚀🎵
