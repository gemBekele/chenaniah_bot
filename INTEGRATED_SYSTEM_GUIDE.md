# Integrated Screening System Guide

This guide explains how to set up and use the new integrated screening system that replaces Google Drive and Google Sheets.

## System Overview

The new system consists of:

1. **Telegram Bot**: Collects applications from users
2. **Local Storage**: Stores audio files on the VPS
3. **SQLite Database**: Stores all application data
4. **REST API**: Provides data to the admin web interface
5. **Web Admin Panel**: Modern UI for reviewing applications

## Key Features

- ✅ No more Google Drive dependencies
- ✅ All data stored on your VPS
- ✅ Fast, seamless audio playback in browser
- ✅ Real-time statistics dashboard
- ✅ Search and filter capabilities
- ✅ Secure admin authentication

## Setup Instructions

### 1. Bot Configuration

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   
   # Database Configuration
   DATABASE_PATH=./vocalist_screening.db
   
   # API Server Configuration
   API_PORT=5000
   API_SECRET_KEY=generate-a-strong-secret-key-here
   BASE_URL=https://your-vps-domain.com
   
   # Admin Credentials
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python database.py
   ```

### 2. Running the Services

You have two options:

#### Option A: Run Both Services Together (Recommended)
```bash
python start_services.py
```

This starts both the Telegram bot and API server in one process.

#### Option B: Run Services Separately

Terminal 1 - API Server:
```bash
python api_server.py
```

Terminal 2 - Telegram Bot:
```bash
python telegram_bot.py
```

### 3. Web Admin Configuration

1. Navigate to the web project:
   ```bash
   cd ../web/chenaniah-web
   ```

2. Create `.env.local`:
   ```bash
   # For local development
   NEXT_PUBLIC_API_URL=http://localhost:5000/api
   
   # For production (update with your VPS domain)
   # NEXT_PUBLIC_API_URL=https://your-vps-domain.com/api
   ```

3. Install dependencies and run:
   ```bash
   npm install
   npm run dev
   ```

4. Access admin panel at: `http://localhost:3000/admin`

## Usage Guide

### For Users (Telegram Bot)

Users interact with the bot exactly as before:

1. `/start` - Begin application
2. Provide name, address, phone, church
3. Upload audio worship sample
4. Submit application

All data is now stored locally on your VPS instead of Google Drive.

### For Admins (Web Dashboard)

1. **Login**:
   - Go to `https://your-domain.com/admin`
   - Use credentials from `.env` file

2. **Dashboard Features**:
   - View statistics (total, pending, approved, rejected)
   - Search applications by name, phone, or church
   - Filter by status (all, pending, approved, rejected)
   
3. **Review Applications**:
   - Click play button to listen to worship sample
   - Audio plays seamlessly in browser
   - View all applicant details
   - Add comments
   - Approve or reject with one click

4. **Audio Playback**:
   - Click play button on any submission
   - Audio streams directly from VPS
   - Pause/resume as needed
   - No downloads required

## API Endpoints

The API server provides these endpoints:

### Authentication
- `POST /api/auth/login` - Login and get JWT token

### Submissions
- `GET /api/submissions` - Get all submissions (with optional status filter)
- `GET /api/submissions/:id` - Get single submission
- `PUT /api/submissions/:id/status` - Update submission status

### Audio
- `GET /api/audio/:file_path` - Stream audio file

### Statistics
- `GET /api/stats` - Get submission statistics

All endpoints (except login) require JWT authentication via `Authorization: Bearer <token>` header.

## File Structure

```
bot/
├── telegram_bot.py          # Main bot logic
├── api_server.py            # REST API server
├── database.py              # Database operations
├── local_storage_service.py # Audio file storage
├── start_services.py        # Service manager
├── vocalist_screening.db    # SQLite database
├── audio_files/             # Audio storage
│   └── YYYY-MM-DD/         # Organized by date
└── .env                     # Configuration

web/chenaniah-web/
├── app/
│   └── admin/
│       └── page.tsx         # Admin route
├── components/
│   ├── admin-login.tsx      # Login component
│   └── admin-dashboard.tsx  # Dashboard UI
└── .env.local               # Web config
```

## Security Considerations

1. **Change default credentials**: Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in production
2. **Use strong secret key**: Generate a random `API_SECRET_KEY`
3. **HTTPS in production**: Always use HTTPS for the API
4. **Firewall**: Only expose necessary ports (443 for web, API port for backend)

## Production Deployment

### VPS Setup

1. Install Python and Node.js
2. Clone repositories
3. Set up environment variables
4. Configure nginx as reverse proxy:

```nginx
# API Server
server {
    listen 80;
    server_name api.your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Web Admin
server {
    listen 80;
    server_name admin.your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. Set up SSL with Let's Encrypt
6. Create systemd services for auto-restart

### Systemd Service Example

Create `/etc/systemd/system/chenaniah-bot.service`:

```ini
[Unit]
Description=Chenaniah Bot Services
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 start_services.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chenaniah-bot
sudo systemctl start chenaniah-bot
```

## Troubleshooting

### Bot not receiving updates
- Check `TELEGRAM_BOT_TOKEN` is correct
- Ensure no other instances are running
- Check logs: `tail -f logs/bot.log`

### API authentication errors
- Verify `API_SECRET_KEY` matches on both bot and web
- Check token expiration (24 hours by default)
- Clear browser localStorage and login again

### Audio not playing
- Check audio files exist in `audio_files/` directory
- Verify API endpoint is accessible
- Check browser console for CORS errors
- Ensure proper MIME type (audio/mpeg)

### Database errors
- Ensure SQLite database file is writable
- Check database file permissions
- Backup database regularly

## Backup Strategy

1. **Database**:
   ```bash
   sqlite3 vocalist_screening.db ".backup backup_$(date +%Y%m%d).db"
   ```

2. **Audio Files**:
   ```bash
   tar -czf audio_backup_$(date +%Y%m%d).tar.gz audio_files/
   ```

3. **Automated Backups**:
   Create a cron job:
   ```bash
   0 2 * * * /path/to/backup_script.sh
   ```

## Monitoring

Check service status:
```bash
# API Server
curl http://localhost:5000/api/health

# Statistics
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/stats
```

## Migration from Old System

If you have existing data in Google Sheets:

1. Export sheet to CSV
2. Create migration script to import into SQLite
3. Audio files on Google Drive need to be downloaded
4. Update audio_file_path references in database

## Support

For issues or questions:
- Check logs in `logs/bot.log`
- Review API responses in browser dev tools
- Ensure all environment variables are set correctly

## Changelog

### Version 2.0 - Integrated System
- Removed Google Drive dependency
- Removed Google Sheets dependency
- Added local audio storage
- Added REST API
- Added web admin dashboard
- Improved audio playback experience
- Enhanced security with JWT authentication

