#!/usr/bin/env python3
"""
Simple API Load Test for Chenaniah System
Tests API endpoints under load without external dependencies
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_load_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleAPILoadTester:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.test_results = []
        
    async def test_api_endpoint(self, endpoint: str, method: str = "GET", 
                              data: Dict[str, Any] = None, 
                              headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Test a single API endpoint"""
        # Fix double slashes issue
        base_url = self.api_base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        url = f"{base_url}/{endpoint}"
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        response_time = time.time() - start_time
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()
                        
                        return {
                            'success': response.status == 200,
                            'status_code': response.status,
                            'response_time': response_time,
                            'data': response_data,
                            'url': url
                        }
                elif method == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        response_time = time.time() - start_time
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()
                        
                        return {
                            'success': response.status == 200,
                            'status_code': response.status,
                            'response_time': response_time,
                            'data': response_data,
                            'url': url
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time,
                'url': url
            }
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test health endpoint"""
        logger.info("Testing health endpoint...")
        result = await self.test_api_endpoint("/api/health")
        return {
            'test_name': 'health_endpoint',
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
    
    async def test_auth_endpoint(self) -> Dict[str, Any]:
        """Test authentication endpoint"""
        logger.info("Testing authentication endpoint...")
        
        # Test login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        result = await self.test_api_endpoint("/api/auth/login", method="POST", data=login_data)
        
        return {
            'test_name': 'auth_endpoint',
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
    
    async def test_protected_endpoints(self, token: str = None) -> Dict[str, Any]:
        """Test protected endpoints"""
        logger.info("Testing protected endpoints...")
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Test stats endpoint
        stats_result = await self.test_api_endpoint("/api/stats", headers=headers)
        
        # Test submissions endpoint
        submissions_result = await self.test_api_endpoint("/api/submissions", headers=headers)
        
        return {
            'test_name': 'protected_endpoints',
            'timestamp': datetime.now().isoformat(),
            'results': {
                'stats': stats_result,
                'submissions': submissions_result
            }
        }
    
    async def run_concurrent_tests(self, num_requests: int = 10, concurrent_limit: int = 5) -> List[Dict[str, Any]]:
        """Run multiple API tests concurrently"""
        logger.info(f"Running {num_requests} concurrent API tests (max {concurrent_limit} concurrent)")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def run_single_test(test_id: int):
            async with semaphore:
                # Test health endpoint
                health_result = await self.test_health_endpoint()
                health_result['test_id'] = test_id
                
                # Test auth endpoint
                auth_result = await self.test_auth_endpoint()
                auth_result['test_id'] = test_id
                
                # Get token if auth was successful
                token = None
                if auth_result['result'].get('success') and auth_result['result'].get('data', {}).get('token'):
                    token = auth_result['result']['data']['token']
                
                # Test protected endpoints
                protected_result = await self.test_protected_endpoints(token)
                protected_result['test_id'] = test_id
                
                return {
                    'test_id': test_id,
                    'timestamp': datetime.now().isoformat(),
                    'health': health_result,
                    'auth': auth_result,
                    'protected': protected_result
                }
        
        # Run tests concurrently
        start_time = time.time()
        tasks = [run_single_test(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Process results
        successful_tests = [r for r in results if isinstance(r, dict)]
        failed_tests = [r for r in results if not isinstance(r, dict)]
        
        total_duration = end_time - start_time
        
        # Calculate statistics
        all_response_times = []
        for result in successful_tests:
            if result.get('health', {}).get('result', {}).get('response_time'):
                all_response_times.append(result['health']['result']['response_time'])
            if result.get('auth', {}).get('result', {}).get('response_time'):
                all_response_times.append(result['auth']['result']['response_time'])
            if result.get('protected', {}).get('results', {}).get('stats', {}).get('response_time'):
                all_response_times.append(result['protected']['results']['stats']['response_time'])
            if result.get('protected', {}).get('results', {}).get('submissions', {}).get('response_time'):
                all_response_times.append(result['protected']['results']['submissions']['response_time'])
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        max_response_time = max(all_response_times) if all_response_times else 0
        min_response_time = min(all_response_times) if all_response_times else 0
        
        test_summary = {
            'test_type': 'api_load_test',
            'total_requests': num_requests,
            'concurrent_limit': concurrent_limit,
            'total_duration': total_duration,
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(successful_tests) / len(results) * 100,
            'response_times': {
                'average': avg_response_time,
                'maximum': max_response_time,
                'minimum': min_response_time,
                'total_samples': len(all_response_times)
            },
            'throughput': len(successful_tests) / total_duration if total_duration > 0 else 0,
            'timestamp': datetime.now().isoformat(),
            'detailed_results': results
        }
        
        self.test_results.append(test_summary)
        
        # Log summary
        logger.info(f"API Load test completed:")
        logger.info(f"  Total requests: {num_requests}")
        logger.info(f"  Successful: {len(successful_tests)}")
        logger.info(f"  Failed: {len(failed_tests)}")
        logger.info(f"  Success rate: {len(successful_tests) / len(results) * 100:.2f}%")
        logger.info(f"  Total duration: {total_duration:.2f}s")
        logger.info(f"  Average response time: {avg_response_time:.3f}s")
        logger.info(f"  Max response time: {max_response_time:.3f}s")
        logger.info(f"  Min response time: {min_response_time:.3f}s")
        logger.info(f"  Throughput: {len(successful_tests) / total_duration:.2f} requests/second")
        
        return test_summary
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if not filename:
            filename = f"api_load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"API load test results saved to {filename}")
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and provide recommendations"""
        if not self.test_results:
            return {'error': 'No test results available'}
        
        latest_result = self.test_results[-1]
        
        # Performance analysis
        success_rate = latest_result.get('success_rate', 0)
        avg_response_time = latest_result.get('response_times', {}).get('average', 0)
        max_response_time = latest_result.get('response_times', {}).get('maximum', 0)
        throughput = latest_result.get('throughput', 0)
        
        # Generate recommendations
        recommendations = []
        
        if success_rate < 90:
            recommendations.append(f"Low success rate ({success_rate:.1f}%). Check API server status and configuration.")
        
        if avg_response_time > 2.0:
            recommendations.append(f"Slow average response time ({avg_response_time:.3f}s). Consider database optimization.")
        
        if max_response_time > 5.0:
            recommendations.append(f"High maximum response time ({max_response_time:.3f}s). Check for blocking operations.")
        
        if throughput < 1.0:
            recommendations.append(f"Low throughput ({throughput:.2f} req/s). Consider scaling or optimization.")
        
        if not recommendations:
            recommendations.append("API performance appears to be within acceptable ranges.")
        
        # Performance rating
        if success_rate >= 95 and avg_response_time <= 1.0 and throughput >= 2.0:
            performance_rating = "Excellent"
        elif success_rate >= 90 and avg_response_time <= 2.0 and throughput >= 1.0:
            performance_rating = "Good"
        elif success_rate >= 80 and avg_response_time <= 3.0 and throughput >= 0.5:
            performance_rating = "Acceptable"
        else:
            performance_rating = "Needs Improvement"
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_rating': performance_rating,
            'metrics': {
                'success_rate': success_rate,
                'average_response_time': avg_response_time,
                'maximum_response_time': max_response_time,
                'throughput': throughput
            },
            'recommendations': recommendations,
            'server_specs': {
                'vps_cores': 4,
                'vps_ram_gb': 8,
                'vps_storage': '75GB NVMe SSD',
                'expected_concurrent_users': '20-30',
                'expected_response_time': '< 1 second'
            }
        }

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple API Load Test')
    parser.add_argument('--api-url', default='https://www.chenaniah.org/api/', help='API base URL')
    parser.add_argument('--requests', type=int, default=20, help='Number of requests to send')
    parser.add_argument('--concurrent', type=int, default=5, help='Max concurrent requests')
    
    args = parser.parse_args()
    
    tester = SimpleAPILoadTester(args.api_url)
    
    try:
        logger.info(f"Starting API load test on {args.api_url}")
        logger.info(f"Requests: {args.requests}, Concurrent: {args.concurrent}")
        
        # Run the load test
        await tester.run_concurrent_tests(args.requests, args.concurrent)
        
        # Save results
        tester.save_results()
        
        # Analyze results
        analysis = tester.analyze_results()
        
        logger.info(f"Performance Rating: {analysis['performance_rating']}")
        logger.info("Recommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            logger.info(f"  {i}. {rec}")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
