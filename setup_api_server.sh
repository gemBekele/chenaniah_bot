#!/bin/bash

echo "🚀 Setting up Chenaniah API Server with WSGI..."

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Please run this script from the bot directory"
    exit 1
fi

# Install gunicorn if not already installed
echo "📦 Installing Gunicorn..."
source venv/bin/activate
pip install gunicorn

# Copy the service file to systemd
echo "🔧 Installing systemd service..."
sudo cp chenaniah-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable chenaniah-api

# Create logs directory if it doesn't exist
mkdir -p logs

# Set proper permissions
sudo chown -R barch:barch /home/barch/chenaniah_bot/logs

echo "✅ API Server setup completed!"
echo ""
echo "🔧 Management Commands:"
echo "  sudo systemctl start chenaniah-api     # Start the API server"
echo "  sudo systemctl stop chenaniah-api      # Stop the API server"
echo "  sudo systemctl restart chenaniah-api   # Restart the API server"
echo "  sudo systemctl status chenaniah-api    # Check status"
echo "  sudo journalctl -u chenaniah-api -f    # View logs"
echo ""
echo "🌐 API will be available at:"
echo "  http://localhost:5000/api/health"
echo "  http://localhost:5000/api/submissions"
echo ""
echo "🔑 Admin credentials (from .env file):"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "⚠️  Remember to update the admin credentials in .env file!"
