#!/usr/bin/env python3
"""
Main script to run the Vocalist Screening Bot
"""

import asyncio
import logging
import signal
import sys
import threading
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from telegram_bot import VocalistScreeningBot
from config import Config

# Create necessary directories first
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self):
        self.bot = None
        self.running = False
        self.health_server = None
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.bot and self.bot.application:
            self.bot.application.stop()
    
    def check_configuration(self):
        """Check if all required configuration is present"""
        missing_config = []
        
        if not Config.TELEGRAM_BOT_TOKEN:
            missing_config.append("TELEGRAM_BOT_TOKEN")
        
        if not Config.GOOGLE_DRIVE_FOLDER_ID:
            missing_config.append("GOOGLE_DRIVE_FOLDER_ID")
        
        if not Config.GOOGLE_SHEET_ID:
            missing_config.append("GOOGLE_SHEET_ID")
        
        # Check for Google credentials (either service account JSON or credentials file)
        if not Config.GOOGLE_SERVICE_ACCOUNT_JSON and not Path(Config.GOOGLE_CREDENTIALS_FILE).exists():
            missing_config.append(f"Google credentials: Either GOOGLE_SERVICE_ACCOUNT_JSON environment variable or {Config.GOOGLE_CREDENTIALS_FILE} file required")
        
        if missing_config:
            logger.error("Missing required configuration:")
            for config in missing_config:
                logger.error(f"  - {config}")
            logger.error("Please check your .env file and credentials.json")
            logger.error("For production deployment, consider using GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            logger.error("Run 'python setup_service_account_env.py' for setup instructions")
            return False
        
        return True
    
    def start_health_server(self):
        """Start health check server for Render"""
        try:
            from health_check import app
            import os
            
            port = int(os.getenv('PORT', 5000))
            self.health_server = threading.Thread(
                target=lambda: app.run(host='0.0.0.0', port=port, debug=False),
                daemon=True
            )
            self.health_server.start()
            logger.info(f"Health check server started on port {port}")
        except Exception as e:
            logger.warning(f"Could not start health server: {e}")

    def run(self):
        """Run the bot"""
        logger.info("Starting Vocalist Screening Bot...")
        
        # Check configuration
        if not self.check_configuration():
            logger.error("Configuration check failed. Exiting.")
            sys.exit(1)
        
        # Start health check server for Render
        self.start_health_server()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Create and run bot
            self.bot = VocalistScreeningBot()
            self.running = True
            
            logger.info("Bot configuration valid. Starting...")
            self.bot.run()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)
        finally:
            logger.info("Bot shutdown complete")

def main():
    """Main entry point"""
    # Run the bot
    runner = BotRunner()
    runner.run()

if __name__ == "__main__":
    main()
