#!/bin/bash

# VPS Optimization Script for High-Pressure Launch
# Run this script on your VPS to optimize for production use

echo "======================================"
echo "VPS OPTIMIZATION FOR PRODUCTION"
echo "======================================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo or as root"
    exit 1
fi

echo "Starting VPS optimizations..."
echo ""

# 1. Increase file descriptor limits
echo "1. Increasing file descriptor limits..."
cat >> /etc/security/limits.conf << EOF

# Increase file descriptor limits for production
* soft nofile 65535
* hard nofile 65535
barch soft nofile 65535
barch hard nofile 65535
EOF

# Also set in current session
ulimit -n 65535

echo "✅ File descriptor limit increased to 65535"
echo ""

# 2. Add swap space if not exists
echo "2. Checking swap space..."
SWAP_EXISTS=$(swapon --show | wc -l)

if [ $SWAP_EXISTS -eq 0 ]; then
    echo "Creating 4GB swap file..."
    
    # Create swap file
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make it permanent
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    
    # Optimize swap usage
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    
    echo "✅ 4GB swap space created and configured"
else
    echo "✅ Swap space already exists"
fi
echo ""

# 3. Optimize SQLite database
echo "3. Optimizing SQLite database..."
DB_PATH="$HOME/chenaniah-bot/vocalist_screening.db"

if [ -f "$DB_PATH" ]; then
    cd $HOME/chenaniah-bot
    
    # Enable WAL mode for better concurrency
    sqlite3 vocalist_screening.db "PRAGMA journal_mode=WAL;" 2>/dev/null
    
    # Optimize database
    sqlite3 vocalist_screening.db "PRAGMA optimize;" 2>/dev/null
    sqlite3 vocalist_screening.db "VACUUM;" 2>/dev/null
    
    echo "✅ Database optimized with WAL mode"
else
    echo "⚠️  Database not found at $DB_PATH"
fi
echo ""

# 4. Optimize network settings
echo "4. Optimizing network settings..."

# Increase max connections
sysctl -w net.core.somaxconn=4096
echo 'net.core.somaxconn=4096' >> /etc/sysctl.conf

# Increase network buffer sizes
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
echo 'net.core.rmem_max=16777216' >> /etc/sysctl.conf
echo 'net.core.wmem_max=16777216' >> /etc/sysctl.conf

# Enable TCP fast open
sysctl -w net.ipv4.tcp_fastopen=3
echo 'net.ipv4.tcp_fastopen=3' >> /etc/sysctl.conf

echo "✅ Network settings optimized"
echo ""

# 5. Optimize Nginx (if installed)
echo "5. Checking Nginx configuration..."

if command -v nginx &> /dev/null; then
    NGINX_CONF="/etc/nginx/nginx.conf"
    
    # Backup original config
    cp $NGINX_CONF ${NGINX_CONF}.backup
    
    # Update worker settings
    sed -i 's/worker_processes.*/worker_processes 4;/' $NGINX_CONF
    sed -i 's/worker_connections.*/worker_connections 2048;/' $NGINX_CONF
    
    # Add optimizations if not present
    if ! grep -q "client_max_body_size" $NGINX_CONF; then
        sed -i '/http {/a \    client_max_body_size 10M;' $NGINX_CONF
    fi
    
    if ! grep -q "keepalive_timeout" $NGINX_CONF; then
        sed -i '/http {/a \    keepalive_timeout 65;' $NGINX_CONF
    fi
    
    # Test and reload
    nginx -t && systemctl reload nginx
    
    echo "✅ Nginx optimized and reloaded"
else
    echo "⚠️  Nginx not installed, skipping"
fi
echo ""

# 6. Install Python performance packages
echo "6. Installing Python performance packages..."

if [ -d "$HOME/chenaniah-bot/venv" ]; then
    cd $HOME/chenaniah-bot
    source venv/bin/activate
    
    # Install psutil for monitoring
    pip install psutil --quiet
    
    echo "✅ Performance packages installed"
else
    echo "⚠️  Virtual environment not found"
fi
echo ""

# 7. Setup log rotation
echo "7. Setting up log rotation..."

cat > /etc/logrotate.d/chenaniah-bot << EOF
$HOME/chenaniah-bot/logs/*.log {
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
EOF

echo "✅ Log rotation configured (7 days)"
echo ""

# 8. Create systemd service with optimizations
echo "8. Creating optimized systemd service..."

cat > /etc/systemd/system/chenaniah-bot.service << EOF
[Unit]
Description=Chenaniah Worship Ministry Bot (Optimized)
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
systemctl daemon-reload

echo "✅ Systemd service created with optimizations"
echo ""

# 9. Create monitoring script
echo "9. Creating monitoring cron job..."

# Create monitoring script
cat > /home/barch/chenaniah-bot/check_bot_health.sh << 'EOF'
#!/bin/bash
# Check if bot is running and restart if needed

BOT_RUNNING=$(pgrep -f telegram_bot_optimized.py)

if [ -z "$BOT_RUNNING" ]; then
    echo "$(date): Bot not running, restarting..." >> /home/barch/chenaniah-bot/logs/health-check.log
    systemctl restart chenaniah-bot
else
    echo "$(date): Bot is running (PID: $BOT_RUNNING)" >> /home/barch/chenaniah-bot/logs/health-check.log
fi
EOF

chmod +x /home/barch/chenaniah-bot/check_bot_health.sh
chown barch:barch /home/barch/chenaniah-bot/check_bot_health.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/barch/chenaniah-bot/check_bot_health.sh") | crontab -u barch -

echo "✅ Health check monitoring setup (every 5 minutes)"
echo ""

# 10. Optimize system for performance
echo "10. Applying final system optimizations..."

# Disable unnecessary services to free up resources
# (Uncomment if you want to be aggressive)
# systemctl disable bluetooth.service
# systemctl disable cups.service

# Optimize file system
echo 'vm.dirty_ratio=10' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
sysctl -w vm.dirty_ratio=10
sysctl -w vm.dirty_background_ratio=5

# Apply all sysctl changes
sysctl -p

echo "✅ System optimizations applied"
echo ""

echo "======================================"
echo "OPTIMIZATION COMPLETE!"
echo "======================================"
echo ""
echo "Summary of optimizations:"
echo "  ✅ File descriptors: 65535"
echo "  ✅ Swap space: 4GB"
echo "  ✅ Database: WAL mode enabled"
echo "  ✅ Network: Optimized for 4096 connections"
echo "  ✅ Nginx: 4 workers, 2048 connections each"
echo "  ✅ Systemd: Configured with auto-restart"
echo "  ✅ Monitoring: Health checks every 5 minutes"
echo "  ✅ Log rotation: 7 days"
echo ""
echo "Next steps:"
echo "  1. Review /etc/security/limits.conf"
echo "  2. Test the bot: systemctl restart chenaniah-bot"
echo "  3. Monitor logs: journalctl -u chenaniah-bot -f"
echo "  4. Check stats with: /stats command in bot"
echo ""
echo "⚠️  IMPORTANT: Logout and login again for file descriptor limits to take effect!"
echo ""

