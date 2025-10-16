#!/usr/bin/env python3
"""
Bot Load Testing Tool for Chenaniah Vocalist Screening Bot
Tests concurrent bot interactions and system performance
"""

import asyncio
import aiohttp
import random
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import argparse
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_load_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BotLoadTester:
    def __init__(self, bot_token: str, api_base_url: str = "http://localhost:5000"):
        self.bot_token = bot_token
        self.api_base_url = api_base_url
        self.test_results = []
        self.session = None
        
    async def create_session(self):
        """Create aiohttp session"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def simulate_bot_conversation(self, user_id: int, test_name: str) -> Dict[str, Any]:
        """Simulate a complete bot conversation"""
        start_time = time.time()
        conversation_steps = []
        errors = []
        
        try:
            # Step 1: Send /start command
            await self.send_telegram_message("/start", user_id)
            conversation_steps.append("start_command")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 2: Send name
            name = f"TestUser{user_id}"
            await self.send_telegram_message(name, user_id)
            conversation_steps.append("name_input")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 3: Send address
            address = f"Test Address {user_id}, Addis Ababa, Ethiopia"
            await self.send_telegram_message(address, user_id)
            conversation_steps.append("address_input")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 4: Send phone
            phone = f"+251{random.randint(900000000, 999999999)}"
            await self.send_telegram_message(phone, user_id)
            conversation_steps.append("phone_input")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 5: Send church
            church = f"Test Church {user_id}"
            await self.send_telegram_message(church, user_id)
            conversation_steps.append("church_input")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Step 6: Send audio file (simulate)
            await self.send_audio_file(user_id)
            conversation_steps.append("audio_upload")
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Step 7: Submit application
            await self.send_callback_query("submit_application", user_id)
            conversation_steps.append("submit_application")
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Error in conversation for user {user_id}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "user_id": user_id,
            "test_name": test_name,
            "duration": duration,
            "steps_completed": len(conversation_steps),
            "conversation_steps": conversation_steps,
            "errors": errors,
            "success": len(errors) == 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_telegram_message(self, text: str, user_id: int):
        """Send a message to the bot via Telegram API"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Telegram API error: {response.status} - {error_text}")
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            raise
    
    async def send_audio_file(self, user_id: int):
        """Simulate sending an audio file"""
        # Create a small test audio file
        test_audio_path = Path("test_audio.mp3")
        if not test_audio_path.exists():
            # Create a minimal MP3 file for testing
            with open(test_audio_path, "wb") as f:
                # Minimal MP3 header
                f.write(b'\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendAudio"
        data = aiohttp.FormData()
        data.add_field('chat_id', str(user_id))
        data.add_field('audio', open(test_audio_path, 'rb'), filename='test_audio.mp3')
        
        try:
            async with self.session.post(url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Telegram API error: {response.status} - {error_text}")
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to send audio to user {user_id}: {e}")
            raise
    
    async def send_callback_query(self, callback_data: str, user_id: int):
        """Simulate callback query (button press)"""
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        data = {
            "callback_query_id": f"test_{user_id}_{int(time.time())}",
            "text": "Test callback"
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Telegram API error: {response.status} - {error_text}")
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to send callback query for user {user_id}: {e}")
            raise
    
    async def run_load_test(self, num_users: int, concurrent_limit: int = 10):
        """Run load test with specified number of users"""
        logger.info(f"Starting load test with {num_users} users, max {concurrent_limit} concurrent")
        
        await self.create_session()
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def run_single_test(user_id: int):
            async with semaphore:
                return await self.simulate_bot_conversation(user_id, f"load_test_{num_users}")
        
        # Generate unique user IDs
        user_ids = [random.randint(100000000, 999999999) for _ in range(num_users)]
        
        # Run tests concurrently
        start_time = time.time()
        tasks = [run_single_test(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        await self.close_session()
        
        # Process results
        successful_tests = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        failed_tests = [r for r in results if not isinstance(r, dict) or not r.get('success', False)]
        
        total_duration = end_time - start_time
        
        # Calculate statistics
        avg_duration = sum(r.get('duration', 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
        success_rate = len(successful_tests) / len(results) * 100
        
        test_summary = {
            "test_type": "load_test",
            "total_users": num_users,
            "concurrent_limit": concurrent_limit,
            "total_duration": total_duration,
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "throughput": len(successful_tests) / total_duration if total_duration > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "detailed_results": results
        }
        
        self.test_results.append(test_summary)
        
        # Log summary
        logger.info(f"Load test completed:")
        logger.info(f"  Total users: {num_users}")
        logger.info(f"  Successful: {len(successful_tests)}")
        logger.info(f"  Failed: {len(failed_tests)}")
        logger.info(f"  Success rate: {success_rate:.2f}%")
        logger.info(f"  Total duration: {total_duration:.2f}s")
        logger.info(f"  Average duration: {avg_duration:.2f}s")
        logger.info(f"  Throughput: {len(successful_tests) / total_duration:.2f} tests/second")
        
        return test_summary
    
    async def run_stress_test(self, duration_minutes: int = 5):
        """Run stress test for specified duration"""
        logger.info(f"Starting stress test for {duration_minutes} minutes")
        
        await self.create_session()
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        test_count = 0
        
        while time.time() < end_time:
            # Run 10 concurrent tests every 30 seconds
            user_ids = [random.randint(100000000, 999999999) for _ in range(10)]
            tasks = [self.simulate_bot_conversation(user_id, f"stress_test_{test_count}") for user_id in user_ids]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = [r for r in results if isinstance(r, dict) and r.get('success', False)]
                logger.info(f"Stress test batch {test_count}: {len(successful)}/10 successful")
                test_count += 1
            except Exception as e:
                logger.error(f"Error in stress test batch {test_count}: {e}")
            
            await asyncio.sleep(30)  # Wait 30 seconds between batches
        
        await self.close_session()
        
        logger.info(f"Stress test completed: {test_count} batches in {duration_minutes} minutes")
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if not filename:
            filename = f"bot_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Test results saved to {filename}")

async def main():
    parser = argparse.ArgumentParser(description='Bot Load Testing Tool')
    parser.add_argument('--token', required=True, help='Telegram Bot Token')
    parser.add_argument('--users', type=int, default=10, help='Number of users for load test')
    parser.add_argument('--concurrent', type=int, default=5, help='Max concurrent requests')
    parser.add_argument('--stress', type=int, help='Run stress test for N minutes')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    
    args = parser.parse_args()
    
    tester = BotLoadTester(args.token, args.api_url)
    
    try:
        if args.stress:
            await tester.run_stress_test(args.stress)
        else:
            await tester.run_load_test(args.users, args.concurrent)
        
        tester.save_results()
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

