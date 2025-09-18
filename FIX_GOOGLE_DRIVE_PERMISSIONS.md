# Fix Google Drive Permissions - URGENT

## 🚨 Issue
The bot is getting `Insufficient permissions for the specified parent` error when trying to upload audio files to Google Drive. **Audio files are REQUIRED for vocalist applications.**

## Root Cause
The service account `chenaniah-bot@chenaniah.iam.gserviceaccount.com` doesn't have permission to upload files to the specified Google Drive folder.

## 🔧 Solution (Follow these steps exactly)

### Step 1: Create or Find Your Google Drive Folder
1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder called "Chenaniah Bot Audio Files" (or use an existing folder)
3. Open the folder and copy the folder ID from the URL
   - The URL will look like: `https://drive.google.com/drive/folders/1ABC123DEF456GHI789JKL`
   - Copy the part after `/folders/`: `1ABC123DEF456GHI789JKL`

### Step 2: Share the Folder with the Service Account
1. Right-click on your Google Drive folder
2. Select "Share" or click the share icon
3. In the "Add people and groups" field, enter: `chenaniah-bot@chenaniah.iam.gserviceaccount.com`
4. Set permissions to "Editor" (not just "Viewer")
5. Click "Send" or "Done"

### Step 3: Update Render Environment Variables
1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Find your bot service and click on it
3. Go to the "Environment" tab
4. Add or update the environment variable:
   - **Key**: `GOOGLE_DRIVE_FOLDER_ID`
   - **Value**: Your folder ID (e.g., `1ABC123DEF456GHI789JKL`)
5. Click "Save Changes"
6. The service will automatically redeploy

### Step 4: Test the Bot
1. Wait for the deployment to complete (2-3 minutes)
2. Test the bot by:
   - Sending `/start` to the bot
   - Providing your name, address, and phone
   - Uploading an audio file
   - Verifying it appears in your Google Drive folder

## ✅ Verification
- The bot should successfully upload audio files to your Google Drive folder
- Users should be able to complete their applications with audio files
- No more permission errors in the logs

## 🆘 If Still Having Issues
1. Double-check the folder ID is correct
2. Ensure the service account has "Editor" permissions (not just "Viewer")
3. Check that the environment variable is set correctly in Render
4. Wait a few minutes for changes to propagate

## 📞 Contact
If you need help, the service account email is: `chenaniah-bot@chenaniah.iam.gserviceaccount.com`
