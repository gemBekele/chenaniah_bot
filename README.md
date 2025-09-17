# 🎤 Vocalist Screening Bot

An automated system for screening vocalists through Telegram, with Google Drive storage and Google Sheets integration for seamless review management.

## ✨ Features

- **Telegram Bot Interface**: Easy-to-use conversation flow for vocalist submissions
- **Google Drive Integration**: Automatic audio file upload and shareable link generation
- **Google Sheets Management**: Centralized submission tracking and review system
- **Real-time Notifications**: Instant alerts for reviewers when new submissions arrive
- **Admin Tools**: Comprehensive management and analytics tools
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- Google Cloud Project with Drive and Sheets APIs enabled
- Google Service Account credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vocalist-screening-bot
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Configure your environment**
   - Edit `.env` file with your actual values
   - Place your Google credentials as `credentials.json`

4. **Run the bot**
   ```bash
   python run_bot.py
   ```

## 📋 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id_here

# Google Sheets Configuration
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_SHEET_RANGE=A:G

# Database Configuration
DATABASE_PATH=./vocalist_screening.db

# Notification Configuration (Optional)
REVIEWER_TELEGRAM_CHAT_ID=your_reviewer_chat_id_here
REVIEWER_EMAIL=reviewer@example.com

# Google API Credentials
GOOGLE_CREDENTIALS_FILE=./credentials.json
```

### Google Cloud Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing

2. **Enable APIs**
   - Enable Google Drive API
   - Enable Google Sheets API

3. **Create Credentials**
   - Go to "Credentials" in the API & Services section
   - Create "OAuth 2.0 Client ID" credentials
   - Download the JSON file and save as `credentials.json`

4. **Set up Google Drive Folder**
   - Create a folder in Google Drive for audio files
   - Right-click → Share → Make accessible to anyone with the link
   - Copy the folder ID from the URL

5. **Set up Google Sheets**
   - Create a new Google Sheet
   - Add column headers: `Name | Address | Phone Number | Telegram Link | Audio Link | Submitted At | Status | Reviewer Comments`
   - Copy the sheet ID from the URL

### Telegram Bot Setup

1. **Create a Bot**
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Follow the instructions to create your bot
   - Copy the bot token

2. **Get Reviewer Chat ID** (Optional)
   - Add your bot to a group or message it directly
   - Use `/start` command
   - Check the logs for the chat ID

## 🎯 Usage

### For Vocalists

1. **Start the process**
   - Find your bot on Telegram
   - Send `/start` command

2. **Provide information**
   - Enter your full name
   - Enter your address
   - Enter your phone number
   - Upload your audio sample (voice note or audio file)

3. **Submit application**
   - Review your information
   - Click "Submit Application"
   - Receive confirmation

### For Reviewers

1. **Access submissions**
   - Open the Google Sheet
   - View all submissions in real-time

2. **Review audio**
   - Click on the "Audio Link" to listen
   - Add comments in the "Reviewer Comments" column
   - Update status (Pending/Approved/Rejected)

3. **Get notifications**
   - Receive Telegram notifications for new submissions
   - Use admin tools for bulk management

## 🛠️ Admin Tools

### Command Line Interface

```bash
# Show submission statistics
python admin_tools.py --stats

# Show pending submissions
python admin_tools.py --pending

# Export submissions to CSV
python admin_tools.py --export submissions.csv

# Sync with Google Sheets
python admin_tools.py --sync

# Clean up old data (older than 30 days)
python admin_tools.py --cleanup 30
```

### Database Management

The bot uses SQLite for local data storage. Key tables:

- **users**: Stores conversation state and user information
- **submissions**: Stores completed submissions with review status

## 🐳 Docker Deployment

### Using Docker Compose

1. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f vocalist-bot
   ```

### Using Docker

1. **Build the image**
   ```bash
   docker build -t vocalist-screening-bot .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name vocalist-bot \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/credentials.json:/app/credentials.json \
     -v $(pwd)/data:/app/data \
     vocalist-screening-bot
   ```

## 📊 Google Sheets Structure

| Column | Description |
|--------|-------------|
| Name | Vocalist's full name |
| Address | Physical address |
| Phone Number | Contact phone number |
| Telegram Link | Link to vocalist's Telegram profile |
| Audio Link | Google Drive link to audio file |
| Submitted At | Timestamp of submission |
| Status | Review status (Pending/Approved/Rejected) |
| Reviewer Comments | Comments from reviewers |

## 🔧 Advanced Configuration

### Custom Scopes

The bot uses these Google API scopes:
- `https://www.googleapis.com/auth/drive.file` - Upload files to Drive
- `https://www.googleapis.com/auth/spreadsheets` - Read/write Sheets

### File Storage

- Audio files are stored in the specified Google Drive folder
- Files are made publicly accessible for easy review
- Local database stores metadata and conversation state

### Notifications

- Telegram notifications for new submissions
- Optional email notifications (requires additional setup)
- Daily summary reports for reviewers

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if `TELEGRAM_BOT_TOKEN` is correct
   - Verify bot is not blocked by users
   - Check logs for error messages

2. **Google API errors**
   - Verify `credentials.json` is valid
   - Check if APIs are enabled in Google Cloud Console
   - Ensure folder/sheet IDs are correct

3. **Database errors**
   - Check if database file is writable
   - Verify `DATABASE_PATH` is correct
   - Check disk space

### Logs

- Bot logs: `logs/bot.log`
- Error logs: Check console output
- Database logs: SQLite logs in console

## 📈 Monitoring

### Health Checks

The bot includes health check endpoints for monitoring:

- Docker health check every 30 seconds
- Database connectivity checks
- Google API connectivity checks

### Metrics

Track these metrics for system health:
- Number of active conversations
- Submission success rate
- Google API quota usage
- Database size and performance

## 🔒 Security

### Data Protection

- Audio files are stored securely in Google Drive
- User data is encrypted in transit
- Database is stored locally (not in cloud)

### Access Control

- Bot access controlled by Telegram
- Google Drive folder access controlled by sharing settings
- Google Sheets access controlled by sharing permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error messages
- Create an issue in the repository

## 🔄 Updates

To update the bot:
1. Pull latest changes
2. Update dependencies: `pip install -r requirements.txt`
3. Restart the bot
4. Check for any configuration changes

---

**Happy Screening! 🎤✨**
