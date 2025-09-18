# Fix Google Drive Permissions

## Issue
The bot is getting `Insufficient permissions for the specified parent` error when trying to upload audio files to Google Drive.

## Root Cause
The service account `chenaniah-bot@chenaniah.iam.gserviceaccount.com` doesn't have permission to upload files to the specified Google Drive folder.

## Solution

### Step 1: Get the Google Drive Folder ID
1. Open the Google Drive folder where you want audio files to be stored
2. Copy the folder ID from the URL (the long string after `/folders/`)
3. Set this as `GOOGLE_DRIVE_FOLDER_ID` in your environment variables

### Step 2: Share the Folder with the Service Account
1. Open the Google Drive folder
2. Right-click and select "Share"
3. Add the service account email: `chenaniah-bot@chenaniah.iam.gserviceaccount.com`
4. Give it "Editor" permissions
5. Click "Send"

### Step 3: Verify Permissions
1. The service account should now be able to upload files to the folder
2. Test by running the bot and trying to upload an audio file

## Alternative: Use a Different Folder
If you can't share the folder, you can:
1. Create a new folder in Google Drive
2. Share it with the service account
3. Update the `GOOGLE_DRIVE_FOLDER_ID` environment variable

## For Render Deployment
Make sure to set the `GOOGLE_DRIVE_FOLDER_ID` environment variable in your Render dashboard with the correct folder ID.

## Testing
After fixing permissions, test the bot by:
1. Starting a new application with `/start`
2. Providing name, address, and phone
3. Uploading an audio file
4. Verifying it appears in the Google Drive folder
