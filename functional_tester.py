#!/usr/bin/env python3
"""
Functional Testing Tool for Chenaniah Bot
Tests individual bot features and API endpoints
"""

import asyncio
import aiohttp
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('functional_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FunctionalTester:
    def __init__(self, bot_token: str, api_base_url: str = "http://localhost:5000"):
        self.bot_token = bot_token
        self.api_base_url = api_base_url
        self.session = None
        self.test_results = []
        
    async def create_session(self):
        """Create aiohttp session"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def test_telegram_bot_commands(self) -> Dict[str, Any]:
        """Test Telegram bot commands"""
        logger.info("Testing Telegram bot commands...")
        
        test_user_id = 123456789  # Test user ID
        results = {}
        
        try:
            # Test /start command
            start_result = await self.send_telegram_command("/start", test_user_id)
            results["start_command"] = {
                "success": start_result.get("ok", False),
                "response": start_result
            }
            
            # Test /help command
            help_result = await self.send_telegram_command("/help", test_user_id)
            results["help_command"] = {
                "success": help_result.get("ok", False),
                "response": help_result
            }
            
            # Test /status command
            status_result = await self.send_telegram_command("/status", test_user_id)
            results["status_command"] = {
                "success": status_result.get("ok", False),
                "response": status_result
            }
            
        except Exception as e:
            logger.error(f"Error testing Telegram commands: {e}")
            results["error"] = str(e)
        
        return {
            "test_name": "telegram_commands",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    
    async def test_conversation_flow(self) -> Dict[str, Any]:
        """Test complete conversation flow"""
        logger.info("Testing conversation flow...")
        
        test_user_id = 987654321  # Different test user ID
        results = {}
        
        try:
            # Step 1: Start conversation
            await self.send_telegram_command("/start", test_user_id)
            await asyncio.sleep(1)
            
            # Step 2: Send name
            name_result = await self.send_telegram_message("Test User", test_user_id)
            results["name_input"] = {
                "success": name_result.get("ok", False),
                "response": name_result
            }
            await asyncio.sleep(1)
            
            # Step 3: Send address
            address_result = await self.send_telegram_message("Test Address, Addis Ababa", test_user_id)
            results["address_input"] = {
                "success": address_result.get("ok", False),
                "response": address_result
            }
            await asyncio.sleep(1)
            
            # Step 4: Send phone
            phone_result = await self.send_telegram_message("+251900000000", test_user_id)
            results["phone_input"] = {
                "success": phone_result.get("ok", False),
                "response": phone_result
            }
            await asyncio.sleep(1)
            
            # Step 5: Send church
            church_result = await self.send_telegram_message("Test Church", test_user_id)
            results["church_input"] = {
                "success": church_result.get("ok", False),
                "response": church_result
            }
            
        except Exception as e:
            logger.error(f"Error testing conversation flow: {e}")
            results["error"] = str(e)
        
        return {
            "test_name": "conversation_flow",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        logger.info("Testing API endpoints...")
        
        results = {}
        
        # Test health endpoint
        try:
            health_result = await self.test_api_endpoint("/api/health")
            results["health"] = health_result
        except Exception as e:
            results["health"] = {"success": False, "error": str(e)}
        
        # Test stats endpoint (requires authentication)
        try:
            stats_result = await self.test_api_endpoint("/api/stats", require_auth=True)
            results["stats"] = stats_result
        except Exception as e:
            results["stats"] = {"success": False, "error": str(e)}
        
        # Test submissions endpoint (requires authentication)
        try:
            submissions_result = await self.test_api_endpoint("/api/submissions", require_auth=True)
            results["submissions"] = submissions_result
        except Exception as e:
            results["submissions"] = {"success": False, "error": str(e)}
        
        return {
            "test_name": "api_endpoints",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test API authentication"""
        logger.info("Testing API authentication...")
        
        results = {}
        
        try:
            # Test login with valid credentials
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            login_result = await self.test_api_endpoint("/api/auth/login", method="POST", data=login_data)
            results["login"] = login_result
            
            if login_result.get("success") and login_result.get("data", {}).get("token"):
                token = login_result["data"]["token"]
                
                # Test authenticated endpoint
                auth_result = await self.test_api_endpoint("/api/stats", headers={"Authorization": f"Bearer {token}"})
                results["authenticated_request"] = auth_result
            else:
                results["authenticated_request"] = {"success": False, "error": "No token received"}
                
        except Exception as e:
            logger.error(f"Error testing authentication: {e}")
            results["error"] = str(e)
        
        return {
            "test_name": "authentication",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    
    async def test_database_operations(self) -> Dict[str, Any]:
        """Test database operations"""
        logger.info("Testing database operations...")
        
        results = {}
        
        try:
            # Test database connection
            import sqlite3
            db_path = "./vocalist_screening.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Test table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                results["tables_exist"] = {
                    "success": True,
                    "tables": [table[0] for table in tables]
                }
                
                # Test user state operations
                test_user_id = 999999999
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (test_user_id,))
                user_exists = cursor.fetchone() is not None
                results["user_state_check"] = {
                    "success": True,
                    "user_exists": user_exists
                }
                
                # Test submissions count
                cursor.execute("SELECT COUNT(*) FROM submissions")
                submission_count = cursor.fetchone()[0]
                results["submissions_count"] = {
                    "success": True,
                    "count": submission_count
                }
                
        except Exception as e:
            logger.error(f"Error testing database operations: {e}")
            results["error"] = str(e)
        
        return {
            "test_name": "database_operations",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    
    async def send_telegram_command(self, command: str, user_id: int) -> Dict[str, Any]:
        """Send a command to the Telegram bot"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": user_id,
            "text": command
        }
        
        async with self.session.post(url, json=data) as response:
            return await response.json()
    
    async def send_telegram_message(self, text: str, user_id: int) -> Dict[str, Any]:
        """Send a message to the Telegram bot"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": user_id,
            "text": text
        }
        
        async with self.session.post(url, json=data) as response:
            return await response.json()
    
    async def test_api_endpoint(self, endpoint: str, method: str = "GET", 
                              data: Dict[str, Any] = None, 
                              headers: Dict[str, str] = None,
                              require_auth: bool = False) -> Dict[str, Any]:
        """Test an API endpoint"""
        # Remove double slashes
        base_url = self.api_base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        url = f"{base_url}/{endpoint}"
        
        try:
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_data = await response.json()
                    return {
                        "success": response.status == 200,
                        "status_code": response.status,
                        "data": response_data
                    }
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json()
                    return {
                        "success": response.status == 200,
                        "status_code": response.status,
                        "data": response_data
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all functional tests"""
        logger.info("Starting functional tests...")
        
        await self.create_session()
        
        tests = [
            self.test_telegram_bot_commands(),
            self.test_conversation_flow(),
            self.test_api_endpoints(),
            self.test_authentication(),
            self.test_database_operations()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        await self.close_session()
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "test_name": f"test_{i}",
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        self.test_results = processed_results
        return processed_results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and provide summary"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get("success", False))
        failed_tests = total_tests - successful_tests
        
        # Analyze individual test results
        test_analysis = {}
        for result in self.test_results:
            test_name = result.get("test_name", "unknown")
            test_analysis[test_name] = {
                "success": result.get("success", False),
                "timestamp": result.get("timestamp"),
                "error": result.get("error")
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_analysis": test_analysis,
            "recommendations": self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for result in self.test_results:
            if not result.get("success", False):
                test_name = result.get("test_name", "unknown")
                error = result.get("error", "Unknown error")
                recommendations.append(f"Fix {test_name}: {error}")
        
        if not recommendations:
            recommendations.append("All functional tests passed successfully!")
        
        return recommendations
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if not filename:
            filename = f"functional_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Functional test results saved to {filename}")
    
    def save_analysis(self, filename: str = None):
        """Save analysis results to JSON file"""
        if not filename:
            filename = f"functional_test_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        analysis = self.analyze_results()
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Functional test analysis saved to {filename}")
        
        # Print summary
        summary = analysis.get("summary", {})
        logger.info(f"Test Summary:")
        logger.info(f"  Total tests: {summary.get('total_tests', 0)}")
        logger.info(f"  Successful: {summary.get('successful_tests', 0)}")
        logger.info(f"  Failed: {summary.get('failed_tests', 0)}")
        logger.info(f"  Success rate: {summary.get('success_rate', 0):.2f}%")

async def main():
    parser = argparse.ArgumentParser(description='Functional Testing Tool')
    parser.add_argument('--token', required=True, help='Telegram Bot Token')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    
    args = parser.parse_args()
    
    tester = FunctionalTester(args.token, args.api_url)
    
    try:
        await tester.run_all_tests()
        tester.save_results()
        tester.save_analysis()
        
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
