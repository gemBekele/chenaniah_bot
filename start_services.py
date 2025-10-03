#!/usr/bin/env python3
"""
Start both the Telegram bot and API server
"""
import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store process references
processes = []

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutting down services...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    sys.exit(0)

def start_service(name, command):
    """Start a service as a subprocess"""
    logger.info(f"Starting {name}...")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processes.append(process)
        logger.info(f"{name} started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        return None

def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Chenaniah Bot Services...")
    
    # Start API server
    api_process = start_service(
        "API Server",
        [sys.executable, "api_server.py"]
    )
    
    # Wait a bit for API to start
    time.sleep(2)
    
    # Start Telegram bot
    bot_process = start_service(
        "Telegram Bot",
        [sys.executable, "telegram_bot.py"]
    )
    
    if not api_process or not bot_process:
        logger.error("Failed to start services")
        signal_handler(None, None)
        return
    
    logger.info("All services started successfully!")
    logger.info("Press Ctrl+C to stop all services")
    
    # Monitor processes
    try:
        while True:
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    logger.error(f"Process {i} has died with code {process.returncode}")
                    # Optionally restart the process here
            
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

