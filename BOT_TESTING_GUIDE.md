# Bot Testing Guide for Chenaniah Vocalist Screening System

This guide explains how to test your bot system using the testing tools I've created for you.

## Testing Tools Overview

I've created three comprehensive testing tools for your system:

1. **Bot Load Tester** (`bot_load_tester.py`) - Tests concurrent bot interactions
2. **Performance Monitor** (`performance_monitor.py`) - Monitors system resources
3. **Functional Tester** (`functional_tester.py`) - Tests individual features

## Prerequisites

### 1. Install Required Dependencies

```bash
cd /home/barch/projects/chenaniah/bot
pip install aiohttp psutil
```

### 2. Get Your Bot Token

You'll need your Telegram bot token. If you don't have it:
1. Message @BotFather on Telegram
2. Use `/mybots` to see your existing bots
3. Select your bot and get the token

### 3. Ensure Services Are Running

Make sure both services are running:
```bash
# Terminal 1 - Bot service
cd /home/barch/projects/chenaniah/bot
python telegram_bot.py

# Terminal 2 - API service  
python api_server.py

# Terminal 3 - Web service
cd /home/barch/projects/chenaniah/web/chenaniah-web
npm run dev
```

## Testing Procedures

### 1. Functional Testing

Test individual features and API endpoints:

```bash
python functional_tester.py --token YOUR_BOT_TOKEN --api-url http://localhost:5000
```

**What it tests:**
- Telegram bot commands (/start, /help, /status)
- Complete conversation flow
- API endpoints (health, stats, submissions)
- Authentication system
- Database operations

**Expected output:**
- Test results saved to `functional_test_results_YYYYMMDD_HHMMSS.json`
- Analysis saved to `functional_test_analysis_YYYYMMDD_HHMMSS.json`
- Console output showing test progress and results

### 2. Load Testing

Test concurrent bot interactions:

```bash
# Test with 20 users, max 5 concurrent
python bot_load_tester.py --token YOUR_BOT_TOKEN --users 20 --concurrent 5

# Test with 50 users, max 10 concurrent
python bot_load_tester.py --token YOUR_BOT_TOKEN --users 50 --concurrent 10

# Run stress test for 5 minutes
python bot_load_tester.py --token YOUR_BOT_TOKEN --stress 5
```

**What it tests:**
- Multiple users interacting with bot simultaneously
- Complete conversation flows under load
- System response times
- Error handling under stress

**Expected output:**
- Test results saved to `bot_test_results_YYYYMMDD_HHMMSS.json`
- Console output showing success rates and performance metrics

### 3. Performance Monitoring

Monitor system resources during testing:

```bash
# Monitor for 10 minutes with 30-second intervals
python performance_monitor.py --api-url http://localhost:5000 --duration 10 --interval 30

# Monitor for 30 minutes with 10-second intervals (more detailed)
python performance_monitor.py --api-url http://localhost:5000 --duration 30 --interval 10
```

**What it monitors:**
- CPU usage
- Memory usage
- Disk usage
- Database performance
- API response times
- Audio file storage

**Expected output:**
- Metrics saved to `performance_metrics_YYYYMMDD_HHMMSS.json`
- Analysis saved to `performance_analysis_YYYYMMDD_HHMMSS.json`
- Real-time console output showing resource usage

## Testing Scenarios

### Scenario 1: Basic Functionality Test
```bash
# Run functional tests first
python functional_tester.py --token YOUR_BOT_TOKEN

# Check results
cat functional_test_analysis_*.json
```

### Scenario 2: Light Load Test
```bash
# Test with 10 users
python bot_load_tester.py --token YOUR_BOT_TOKEN --users 10 --concurrent 3

# Monitor performance during test
python performance_monitor.py --duration 5 --interval 15
```

### Scenario 3: Heavy Load Test
```bash
# Test with 50 users
python bot_load_tester.py --token YOUR_BOT_TOKEN --users 50 --concurrent 10

# Monitor performance during test
python performance_monitor.py --duration 15 --interval 10
```

### Scenario 4: Stress Test
```bash
# Run stress test for 10 minutes
python bot_load_tester.py --token YOUR_BOT_TOKEN --stress 10

# Monitor performance during stress test
python performance_monitor.py --duration 10 --interval 5
```

## Interpreting Results

### Functional Test Results
- **Success Rate**: Should be 100% for all tests
- **API Response Times**: Should be under 2 seconds
- **Database Operations**: Should complete without errors

### Load Test Results
- **Success Rate**: Should be above 90%
- **Average Duration**: Should be under 30 seconds per conversation
- **Throughput**: Should handle at least 1-2 conversations per second

### Performance Monitor Results
- **CPU Usage**: Should stay under 80% average
- **Memory Usage**: Should stay under 80% average
- **API Response Times**: Should stay under 2 seconds
- **Database Size**: Monitor for growth

## Troubleshooting

### Common Issues

1. **Bot Token Error**
   ```
   Error: Telegram API error: 401 - Unauthorized
   ```
   **Solution**: Check your bot token is correct

2. **API Connection Error**
   ```
   Error: Connection refused
   ```
   **Solution**: Ensure API server is running on port 5000

3. **Database Error**
   ```
   Error: database is locked
   ```
   **Solution**: Stop other processes using the database

4. **High Memory Usage**
   ```
   Memory usage: 95%
   ```
   **Solution**: Reduce concurrent users or optimize code

### Performance Issues

1. **Slow API Responses**
   - Check database performance
   - Monitor CPU usage
   - Consider database optimization

2. **High Memory Usage**
   - Check for memory leaks
   - Monitor audio file processing
   - Consider file streaming

3. **Database Bottlenecks**
   - Monitor concurrent database access
   - Consider connection pooling
   - Check for long-running queries

## Best Practices

### Before Testing
1. **Backup your database**
2. **Ensure sufficient disk space**
3. **Close unnecessary applications**
4. **Monitor system resources**

### During Testing
1. **Start with small loads**
2. **Monitor system resources**
3. **Watch for error messages**
4. **Document any issues**

### After Testing
1. **Analyze results thoroughly**
2. **Identify bottlenecks**
3. **Plan optimizations**
4. **Document findings**

## Automated Testing Script

Create a simple script to run all tests:

```bash
#!/bin/bash
# test_all.sh

echo "Starting comprehensive bot testing..."

# Get bot token from user
read -p "Enter your bot token: " BOT_TOKEN

# Run functional tests
echo "Running functional tests..."
python functional_tester.py --token $BOT_TOKEN

# Run light load test
echo "Running light load test..."
python bot_load_tester.py --token $BOT_TOKEN --users 10 --concurrent 3

# Run performance monitoring
echo "Running performance monitoring..."
python performance_monitor.py --duration 5 --interval 15 &

# Run heavy load test
echo "Running heavy load test..."
python bot_load_tester.py --token $BOT_TOKEN --users 30 --concurrent 8

# Stop performance monitoring
pkill -f performance_monitor.py

echo "Testing completed! Check the generated JSON files for results."
```

## Expected Performance Benchmarks

Based on your VPS specifications (4 vCores, 8GB RAM, NVMe SSD):

### Good Performance
- **Concurrent Users**: 20-30
- **API Response Time**: < 1 second
- **CPU Usage**: < 60%
- **Memory Usage**: < 70%
- **Success Rate**: > 95%

### Acceptable Performance
- **Concurrent Users**: 10-20
- **API Response Time**: < 2 seconds
- **CPU Usage**: < 80%
- **Memory Usage**: < 80%
- **Success Rate**: > 90%

### Poor Performance (Needs Optimization)
- **Concurrent Users**: < 10
- **API Response Time**: > 3 seconds
- **CPU Usage**: > 90%
- **Memory Usage**: > 90%
- **Success Rate**: < 85%

## Next Steps

After running tests:

1. **Analyze Results**: Review all generated JSON files
2. **Identify Bottlenecks**: Look for performance issues
3. **Optimize Code**: Address identified problems
4. **Re-test**: Run tests again to verify improvements
5. **Document**: Keep records of performance improvements

This testing framework will help you understand your system's capabilities and identify areas for optimization.

