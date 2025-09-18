#!/bin/bash

# Deploy Vocalist Screening Bot to Render.com
# Make sure you have git configured and your code pushed to GitHub

echo "🚀 Deploying Vocalist Screening Bot to Render.com"
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git not initialized. Please run:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo "   git remote add origin YOUR_GITHUB_REPO_URL"
    echo "   git push -u origin main"
    exit 1
fi

# Check if all required files exist
echo "📋 Checking required files..."

required_files=(
    "run_bot.py"
    "telegram_bot.py"
    "google_services.py"
    "requirements.txt"
    "render.yaml"
    "Procfile"
    "runtime.txt"
    "health_check.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found"
    echo "   Make sure to upload it to Render after deployment"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Make sure to set environment variables in Render"
fi

echo ""
echo "📦 Pushing to GitHub..."
git add .
git commit -m "Deploy to Render.com - $(date)"
git push origin main

echo ""
echo "✅ Code pushed to GitHub!"
echo ""
echo "🌐 Next Steps:"
echo "1. Go to https://render.com"
echo "2. Create new Web Service"
echo "3. Connect your GitHub repository"
echo "4. Use these settings:"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: python run_bot.py"
echo "5. Set environment variables (see DEPLOYMENT_GUIDE.md)"
echo "6. Upload credentials.json file"
echo "7. Deploy!"
echo ""
echo "📚 See DEPLOYMENT_GUIDE.md for detailed instructions"
