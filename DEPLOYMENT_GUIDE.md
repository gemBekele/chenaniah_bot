# 🚀 Deploy Chenaniah Worship Ministry Application Bot on Render.com

## 📋 **Prerequisites**

Before deploying, make sure you have:
- ✅ **Render.com account** (free tier available)
- ✅ **GitHub repository** with your bot code
- ✅ **Google Cloud credentials** (credentials.json)
- ✅ **Telegram Bot Token**
- ✅ **Google Drive folder ID**
- ✅ **Google Sheet ID**

## 🔧 **Step 1: Prepare Your Repository**

### **1.1 Push to GitHub**
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Vocalist Screening Bot"

# Add your GitHub repository
git remote add origin https://github.com/yourusername/vocalist-screening-bot.git
git push -u origin main
```

### **1.2 Verify Required Files**
Make sure these files are in your repository:
- ✅ `run_bot.py` - Main bot runner
- ✅ `telegram_bot.py` - Bot implementation
- ✅ `google_services.py` - Google APIs integration
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process definition
- ✅ `runtime.txt` - Python version
- ✅ `.renderignore` - Ignore files

## 🌐 **Step 2: Deploy on Render.com**

### **2.1 Create New Web Service**
1. **Go to [Render.com](https://render.com)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Select your repository**

### **2.2 Configure the Service**
Fill in these details:

**Basic Settings:**
- **Name**: `vocalist-screening-bot`
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python run_bot.py`

**Advanced Settings:**
- **Plan**: `Free` (or upgrade if needed)
- **Auto-Deploy**: `Yes` (for automatic updates)

### **2.3 Set Environment Variables**
Add these environment variables in Render:

| Key | Value | Description |
|-----|-------|-------------|
| `TELEGRAM_BOT_TOKEN` | `your_bot_token` | Your Telegram bot token |
| `GOOGLE_DRIVE_FOLDER_ID` | `your_folder_id` | Google Drive folder ID |
| `GOOGLE_SHEET_ID` | `your_sheet_id` | Google Sheet ID |
| `GOOGLE_SHEET_RANGE` | `A:G` | Sheet range |
| `DATABASE_PATH` | `./data/vocalist_screening.db` | Database path |
| `REVIEWER_TELEGRAM_CHAT_ID` | `your_chat_id` | Optional: Reviewer notifications |
| `REVIEWER_EMAIL` | `reviewer@example.com` | Optional: Email notifications |
| `GOOGLE_CREDENTIALS_FILE` | `./credentials.json` | Google credentials path |

### **2.4 Upload Google Credentials**
1. **Go to your service dashboard**
2. **Click "Files" tab**
3. **Upload `credentials.json`** to the root directory
4. **Make sure it's named exactly `credentials.json`**

## 🔐 **Step 3: Google Cloud Setup**

### **3.1 Update OAuth Redirect URIs**
1. **Go to [Google Cloud Console](https://console.cloud.google.com)**
2. **Navigate to APIs & Services → Credentials**
3. **Edit your OAuth 2.0 Client ID**
4. **Add authorized redirect URI:**
   ```
   https://your-app-name.onrender.com/oauth2callback
   ```
5. **Save changes**

### **3.2 Test Google APIs**
Make sure these APIs are enabled:
- ✅ **Google Drive API**
- ✅ **Google Sheets API**

## 🚀 **Step 4: Deploy and Test**

### **4.1 Deploy**
1. **Click "Create Web Service"**
2. **Wait for deployment** (5-10 minutes)
3. **Check build logs** for any errors

### **4.2 Test the Bot**
1. **Find your bot on Telegram**
2. **Send `/start` command**
3. **Test the full submission process**
4. **Check Google Sheet** for new entries

## 📊 **Step 5: Monitor and Maintain**

### **5.1 Monitor Logs**
- **Go to your service dashboard**
- **Click "Logs" tab**
- **Monitor for errors or issues**

### **5.2 Database Persistence**
- **Render provides persistent disk storage**
- **Database file is stored in `/opt/render/project/data/`**
- **Data persists between deployments**

### **5.3 Updates**
- **Push changes to GitHub**
- **Render automatically redeploys**
- **No manual intervention needed**

## 🔧 **Troubleshooting**

### **Common Issues:**

**1. Bot Not Responding**
- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify bot is not blocked
- Check logs for errors

**2. Google API Errors**
- Verify `credentials.json` is uploaded
- Check Google Cloud project settings
- Ensure APIs are enabled

**3. Database Issues**
- Check `DATABASE_PATH` is correct
- Verify disk storage is mounted
- Check file permissions

**4. Build Failures**
- Check `requirements.txt` syntax
- Verify Python version compatibility
- Check build logs for specific errors

### **Debug Commands:**
```bash
# Check if bot is running
curl https://your-app-name.onrender.com/health

# View logs
# Go to Render dashboard → Logs tab
```

## 💰 **Pricing**

**Free Tier:**
- ✅ **750 hours/month** (enough for 24/7 operation)
- ✅ **512MB RAM**
- ✅ **1GB disk storage**
- ✅ **Automatic deployments**

**Paid Plans:**
- **Starter**: $7/month - More resources
- **Standard**: $25/month - Better performance
- **Pro**: $85/month - High availability

## 🎯 **Production Checklist**

Before going live:
- ✅ **Test all bot commands**
- ✅ **Verify Google Sheets integration**
- ✅ **Test audio upload and playback**
- ✅ **Check notification system**
- ✅ **Monitor logs for 24 hours**
- ✅ **Set up error monitoring**
- ✅ **Create backup strategy**

## 📱 **Mobile Considerations**

- **Bot works on all devices**
- **Google Drive links work on mobile**
- **Consider mobile-friendly sheet layout**
- **Test on different screen sizes**

## 🔄 **Backup Strategy**

1. **Database backups** (automatic with Render)
2. **Google Drive** (automatic with Google)
3. **Google Sheets** (automatic with Google)
4. **Code backups** (automatic with GitHub)

## 🎉 **Success!**

Your Vocalist Screening Bot is now deployed and running on Render.com! 

**Next Steps:**
1. **Share the bot link** with vocalists
2. **Train reviewers** on using Google Sheets
3. **Monitor performance** and usage
4. **Scale up** if needed

---

**Need Help?**
- Check Render documentation
- Review bot logs
- Test locally first
- Contact support if needed
