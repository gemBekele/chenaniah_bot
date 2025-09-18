# VPS Deployment Guide for Chenaniah Bot

## 🚀 **Quick Start Commands**

Connect to your VPS and run these commands:

```bash
# Connect to VPS
ssh barch@15.204.227.47

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx -y

# Create bot directory
mkdir -p ~/chenaniah-bot
cd ~/chenaniah-bot

# Clone your repository
git clone https://github.com/gemBekele/chenaniah_bot.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data temp exports audio_files

# Set up environment variables
nano .env
```

## 📝 **Environment Variables Setup**

Create a `.env` file with these variables:

```bash
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
```

## 🔧 **Service Account Setup (Optional)**

If you want to use Google Drive:

```bash
# Upload your service account file
scp chenaniah-7c3ca849acfa.json barch@15.204.227.47:~/chenaniah-bot/

# Or create it directly on the server
nano chenaniah-7c3ca849acfa.json
# Paste your service account JSON content
```

## 🚀 **Run the Bot**

```bash
# Test the bot first
python run_bot.py

# If it works, create a systemd service for auto-start
sudo nano /etc/systemd/system/chenaniah-bot.service
```

## 📋 **Systemd Service File**

Create `/etc/systemd/system/chenaniah-bot.service`:

```ini
[Unit]
Description=Chenaniah Worship Ministry Bot
After=network.target

[Service]
Type=simple
User=barch
WorkingDirectory=/home/barch/chenaniah-bot
Environment=PATH=/home/barch/chenaniah-bot/venv/bin
ExecStart=/home/barch/chenaniah-bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🌐 **Nginx Configuration**

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/chenaniah-bot

# Add this content:
server {
    listen 80;
    server_name 15.204.227.47;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /audio_files/ {
        alias /home/barch/chenaniah-bot/audio_files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Enable the site
sudo ln -s /etc/nginx/sites-available/chenaniah-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 **SSL Certificate (Optional but Recommended)**

```bash
# Get SSL certificate
sudo certbot --nginx -d 15.204.227.47

# Or use Let's Encrypt
sudo certbot certonly --nginx -d 15.204.227.47
```

## 🎯 **Start Everything**

```bash
# Enable and start the bot service
sudo systemctl enable chenaniah-bot
sudo systemctl start chenaniah-bot

# Check status
sudo systemctl status chenaniah-bot

# View logs
journalctl -u chenaniah-bot -f
```

## ✅ **Verification**

1. **Check if bot is running:**
   ```bash
   curl http://15.204.227.47
   ```

2. **Test audio file serving:**
   ```bash
   curl http://15.204.227.47/audio_files/
   ```

3. **Check bot logs:**
   ```bash
   journalctl -u chenaniah-bot -f
   ```

## 🆘 **Troubleshooting**

### Bot won't start:
```bash
# Check logs
journalctl -u chenaniah-bot -f

# Check if port is in use
sudo netstat -tlnp | grep :5000

# Restart service
sudo systemctl restart chenaniah-bot
```

### Permission issues:
```bash
# Fix ownership
sudo chown -R barch:barch /home/barch/chenaniah-bot
```

### Nginx issues:
```bash
# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

## 🎉 **Success!**

Your bot should now be running at:
- **HTTP**: http://15.204.227.47
- **HTTPS**: https://15.204.227.47 (if SSL is set up)
- **Audio files**: http://15.204.227.47/audio_files/

The bot will:
- ✅ Store audio files permanently
- ✅ Work exactly like locally
- ✅ Auto-restart if it crashes
- ✅ Serve files via HTTP
- ✅ Run 24/7
