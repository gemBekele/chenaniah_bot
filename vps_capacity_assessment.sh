#!/bin/bash

# VPS Capacity Assessment Script
# This script collects all necessary information to assess VPS capacity
# for hosting both the Chenaniah Bot and Web Application

echo "======================================"
echo "VPS CAPACITY ASSESSMENT"
echo "======================================"
echo "Timestamp: $(date)"
echo ""

echo "======================================"
echo "1. HARDWARE SPECIFICATIONS"
echo "======================================"

# CPU Information
echo "CPU Information:"
echo "  Model: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs)"
echo "  Cores: $(nproc)"
echo "  Architecture: $(uname -m)"
echo "  CPU MHz: $(cat /proc/cpuinfo | grep 'cpu MHz' | head -1 | cut -d':' -f2 | xargs)"
echo ""

# Memory Information
echo "Memory Information:"
TOTAL_RAM_KB=$(cat /proc/meminfo | grep MemTotal | awk '{print $2}')
TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
TOTAL_RAM_GB=$(echo "scale=2; $TOTAL_RAM_KB / 1024 / 1024" | bc)
echo "  Total RAM: ${TOTAL_RAM_MB} MB (${TOTAL_RAM_GB} GB)"

AVAILABLE_RAM_KB=$(cat /proc/meminfo | grep MemAvailable | awk '{print $2}')
AVAILABLE_RAM_MB=$((AVAILABLE_RAM_KB / 1024))
echo "  Available RAM: ${AVAILABLE_RAM_MB} MB"

FREE_RAM_KB=$(cat /proc/meminfo | grep MemFree | awk '{print $2}')
FREE_RAM_MB=$((FREE_RAM_KB / 1024))
echo "  Free RAM: ${FREE_RAM_MB} MB"

USED_RAM_MB=$((TOTAL_RAM_MB - AVAILABLE_RAM_MB))
echo "  Used RAM: ${USED_RAM_MB} MB"

SWAP_TOTAL_KB=$(cat /proc/meminfo | grep SwapTotal | awk '{print $2}')
SWAP_TOTAL_MB=$((SWAP_TOTAL_KB / 1024))
echo "  Total Swap: ${SWAP_TOTAL_MB} MB"
echo ""

# Disk Information
echo "Disk Information:"
df -h / | tail -1 | awk '{printf "  Root Filesystem: %s total, %s used, %s available (%s used)\n", $2, $3, $4, $5}'
DISK_AVAILABLE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo ""

echo "======================================"
echo "2. CURRENT RESOURCE USAGE"
echo "======================================"

# System Load
echo "System Load Average:"
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | xargs)
echo "  Load Average: ${LOAD_AVG}"
echo ""

# CPU Usage
echo "Current CPU Usage:"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo "  CPU Usage: ${CPU_USAGE}%"
echo ""

# Memory Usage Percentage
MEM_USAGE_PERCENT=$(echo "scale=2; ($USED_RAM_MB * 100) / $TOTAL_RAM_MB" | bc)
echo "Memory Usage:"
echo "  Memory Usage: ${MEM_USAGE_PERCENT}%"
echo ""

# Top processes
echo "Top 5 CPU-consuming processes:"
ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf "  %-10s %-6s %-6s %s\n", $1, $3"%", $4"%", $11}'
echo ""

echo "Top 5 Memory-consuming processes:"
ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "  %-10s %-6s %-6s %s\n", $1, $3"%", $4"%", $11}'
echo ""

echo "======================================"
echo "3. NETWORK CONFIGURATION"
echo "======================================"

# Network limits
echo "Network Limits:"
MAX_CONNECTIONS=$(cat /proc/sys/net/core/somaxconn)
echo "  Max socket connections: ${MAX_CONNECTIONS}"

FILE_DESCRIPTORS=$(ulimit -n)
echo "  File descriptor limit: ${FILE_DESCRIPTORS}"

MAX_FILE_DESCRIPTORS=$(cat /proc/sys/fs/file-max)
echo "  System max file descriptors: ${MAX_FILE_DESCRIPTORS}"

MAX_THREADS=$(cat /proc/sys/kernel/threads-max)
echo "  System max threads: ${MAX_THREADS}"
echo ""

# Active connections
echo "Current Network Connections:"
ESTABLISHED_CONN=$(netstat -an 2>/dev/null | grep ESTABLISHED | wc -l)
echo "  Established connections: ${ESTABLISHED_CONN}"

LISTEN_PORTS=$(netstat -tuln 2>/dev/null | grep LISTEN | wc -l)
echo "  Listening ports: ${LISTEN_PORTS}"
echo ""

echo "======================================"
echo "4. RUNNING SERVICES"
echo "======================================"

# Check if bot is running
echo "Bot Service Status:"
if pgrep -f run_bot.py > /dev/null; then
    BOT_PID=$(pgrep -f run_bot.py)
    BOT_MEM=$(ps -p $BOT_PID -o rss= | awk '{print $1/1024}')
    BOT_CPU=$(ps -p $BOT_PID -o %cpu=)
    echo "  Status: RUNNING (PID: $BOT_PID)"
    echo "  Memory: ${BOT_MEM} MB"
    echo "  CPU: ${BOT_CPU}%"
else
    echo "  Status: NOT RUNNING"
fi
echo ""

# Check if nginx is running
echo "Web Server Status:"
if pgrep -f nginx > /dev/null; then
    NGINX_PID=$(pgrep -f nginx | head -1)
    NGINX_MEM=$(ps -p $NGINX_PID -o rss= | awk '{print $1/1024}')
    echo "  Nginx Status: RUNNING (PID: $NGINX_PID)"
    echo "  Nginx Memory: ${NGINX_MEM} MB"
else
    echo "  Nginx Status: NOT RUNNING"
fi
echo ""

# Check if Python processes are running
echo "Python Processes:"
PYTHON_COUNT=$(ps aux | grep python | grep -v grep | wc -l)
echo "  Active Python processes: ${PYTHON_COUNT}"
if [ $PYTHON_COUNT -gt 0 ]; then
    ps aux | grep python | grep -v grep | awk '{printf "  %-10s %-6s %-6s %s\n", $1, $3"%", $4"%", $11}' | head -5
fi
echo ""

# Check Node.js processes (for Next.js web app)
echo "Node.js Processes:"
NODE_COUNT=$(ps aux | grep node | grep -v grep | wc -l)
echo "  Active Node.js processes: ${NODE_COUNT}"
if [ $NODE_COUNT -gt 0 ]; then
    ps aux | grep node | grep -v grep | awk '{printf "  %-10s %-6s %-6s %s\n", $1, $3"%", $4"%", $11}' | head -5
fi
echo ""

echo "======================================"
echo "5. STORAGE USAGE"
echo "======================================"

# Bot directory
if [ -d "$HOME/chenaniah-bot" ]; then
    echo "Bot Directory:"
    cd $HOME/chenaniah-bot
    echo "  Location: $HOME/chenaniah-bot"
    echo "  Total size: $(du -sh . 2>/dev/null | cut -f1)"
    
    if [ -f "vocalist_screening.db" ]; then
        DB_SIZE=$(ls -lh vocalist_screening.db | awk '{print $5}')
        echo "  Database size: ${DB_SIZE}"
    fi
    
    if [ -d "audio_files" ]; then
        AUDIO_COUNT=$(find audio_files -type f 2>/dev/null | wc -l)
        AUDIO_SIZE=$(du -sh audio_files 2>/dev/null | cut -f1)
        echo "  Audio files count: ${AUDIO_COUNT}"
        echo "  Audio storage: ${AUDIO_SIZE}"
    fi
    
    if [ -d "logs" ]; then
        LOGS_SIZE=$(du -sh logs 2>/dev/null | cut -f1)
        echo "  Logs size: ${LOGS_SIZE}"
    fi
    echo ""
fi

# Web directory
if [ -d "$HOME/projects/chenaniah/web/chenaniah-web" ]; then
    echo "Web Application Directory:"
    echo "  Location: $HOME/projects/chenaniah/web/chenaniah-web"
    WEB_SIZE=$(du -sh $HOME/projects/chenaniah/web/chenaniah-web 2>/dev/null | cut -f1)
    echo "  Total size: ${WEB_SIZE}"
    echo ""
fi

echo "======================================"
echo "6. DATABASE STATISTICS"
echo "======================================"

if [ -f "$HOME/chenaniah-bot/vocalist_screening.db" ]; then
    cd $HOME/chenaniah-bot
    echo "Database Statistics:"
    
    TOTAL_SUBMISSIONS=$(sqlite3 vocalist_screening.db "SELECT COUNT(*) FROM submissions;" 2>/dev/null || echo "0")
    echo "  Total submissions: ${TOTAL_SUBMISSIONS}"
    
    PENDING_SUBMISSIONS=$(sqlite3 vocalist_screening.db "SELECT COUNT(*) FROM submissions WHERE status='pending';" 2>/dev/null || echo "0")
    echo "  Pending submissions: ${PENDING_SUBMISSIONS}"
    
    TOTAL_USERS=$(sqlite3 vocalist_screening.db "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    echo "  Total users: ${TOTAL_USERS}"
    
    echo ""
fi

echo "======================================"
echo "7. SYSTEM UPTIME & STABILITY"
echo "======================================"

echo "System Uptime:"
uptime -p
echo ""

echo "System Info:"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Kernel: $(uname -r)"
echo ""

echo "======================================"
echo "8. CAPACITY SUMMARY"
echo "======================================"

echo "Resource Summary:"
echo "  CPU Cores: $(nproc)"
echo "  Total RAM: ${TOTAL_RAM_MB} MB (${TOTAL_RAM_GB} GB)"
echo "  Available RAM: ${AVAILABLE_RAM_MB} MB"
echo "  Disk Available: ${DISK_AVAILABLE} GB"
echo "  CPU Usage: ${CPU_USAGE}%"
echo "  Memory Usage: ${MEM_USAGE_PERCENT}%"
echo "  Max File Descriptors: ${FILE_DESCRIPTORS}"
echo "  Max Socket Connections: ${MAX_CONNECTIONS}"
echo ""

echo "======================================"
echo "ASSESSMENT COMPLETE"
echo "======================================"
echo ""
echo "Save this output and share it for capacity analysis."

