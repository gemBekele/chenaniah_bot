# Setup Google Drive Shared Drive - REQUIRED

## 🚨 **CRITICAL ISSUE IDENTIFIED**

The error `Service Accounts do not have storage quota` means that **Service Accounts cannot store files in regular Google Drive folders**. This is a Google Drive limitation.

## ✅ **SOLUTION: Use Google Drive Shared Drives**

Service Accounts CAN store files in **Shared Drives** (formerly Team Drives). Here's how to set it up:

## 🔧 **Step-by-Step Setup**

### **Step 1: Create a Shared Drive**

1. Go to [Google Drive](https://drive.google.com)
2. Click "New" → "Shared drive" (or "Team drive" in older versions)
3. Name it "Chenaniah Bot Audio Files"
4. Click "Create"

### **Step 2: Add the Service Account to the Shared Drive**

1. Open your newly created Shared Drive
2. Click on the Shared Drive name at the top
3. Click "Manage members" or the settings icon
4. Click "Add members"
5. Add this email: `chenaniah-bot@chenaniah.iam.gserviceaccount.com`
6. Set role to "Content manager" (this gives full access)
7. Click "Send"

### **Step 3: Create a Folder in the Shared Drive**

1. Inside your Shared Drive, click "New" → "Folder"
2. Name it "Audio Submissions" (or any name you prefer)
3. Open the folder
4. Copy the folder ID from the URL

The URL will look like:
```
https://drive.google.com/drive/folders/1ABC123DEF456GHI789JKL
```
Copy the part after `/folders/`: `1ABC123DEF456GHI789JKL`

### **Step 4: Update Render Environment Variables**

1. Go to your [Render Dashboard](https://dashboard.render.com)
2. Find your bot service
3. Go to "Environment" tab
4. Update `GOOGLE_DRIVE_FOLDER_ID` with your new folder ID
5. Save changes

### **Step 5: Test the Setup**

Run the test script to verify everything works:

```bash
python test_google_drive.py
```

## 🔍 **How to Identify a Shared Drive**

- **Shared Drive URL**: `https://drive.google.com/drive/folders/DRIVE_ID`
- **Regular Folder URL**: `https://drive.google.com/drive/folders/FOLDER_ID`
- **Shared Drives** have a different icon and show "Shared drive" in the interface

## ⚠️ **Important Notes**

1. **Service Accounts CANNOT** store files in regular Google Drive folders
2. **Service Accounts CAN** store files in Shared Drives
3. The service account must be added as a **Content manager** (not just Viewer)
4. The folder must be **inside** the Shared Drive

## 🆘 **Troubleshooting**

### If you get "File not found" error:
- Make sure you're using a folder ID from **inside** the Shared Drive
- Verify the service account has access to the Shared Drive

### If you get "Insufficient permissions" error:
- Make sure the service account is added to the Shared Drive
- Set the role to "Content manager" (not just "Viewer")

### If you get "Storage quota exceeded" error:
- You're still using a regular folder instead of a Shared Drive
- Create a Shared Drive and use a folder inside it

## 📞 **Need Help?**

The service account email is: `chenaniah-bot@chenaniah.iam.gserviceaccount.com`

Make sure to:
1. Create a **Shared Drive** (not a regular folder)
2. Add the service account as **Content manager**
3. Create a folder **inside** the Shared Drive
4. Use that folder ID in your environment variables
