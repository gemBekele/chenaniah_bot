#!/bin/bash

# Simple VPS Capacity Assessment (no external dependencies)
echo "======================================"
echo "VPS CAPACITY ASSESSMENT - SIMPLE"
echo "======================================"
date
echo ""

echo "=== CPU ==="
echo "Cores: $(nproc)"
cat /proc/cpuinfo | grep 'model name' | head -1
echo ""

echo "=== MEMORY ==="
free -h
echo ""

echo "=== DISK ==="
df -h /
echo ""

echo "=== LOAD ==="
uptime
echo ""

echo "=== TOP PROCESSES ==="
echo "By CPU:"
ps aux --sort=-%cpu | head -6
echo ""
echo "By Memory:"
ps aux --sort=-%mem | head -6
echo ""

echo "=== NETWORK LIMITS ==="
echo "Max connections: $(cat /proc/sys/net/core/somaxconn)"
echo "File descriptors: $(ulimit -n)"
echo "Max file descriptors: $(cat /proc/sys/fs/file-max)"
echo ""

echo "=== SERVICES ==="
echo "Bot running: $(pgrep -f run_bot.py > /dev/null && echo 'YES' || echo 'NO')"
echo "Nginx running: $(pgrep nginx > /dev/null && echo 'YES' || echo 'NO')"
echo "Node.js running: $(pgrep node > /dev/null && echo 'YES' || echo 'NO')"
echo ""

echo "=== STORAGE ==="
if [ -d "$HOME/chenaniah-bot" ]; then
    echo "Bot directory:"
    du -sh $HOME/chenaniah-bot
    [ -f "$HOME/chenaniah-bot/vocalist_screening.db" ] && ls -lh $HOME/chenaniah-bot/vocalist_screening.db
    [ -d "$HOME/chenaniah-bot/audio_files" ] && echo "Audio files:" && du -sh $HOME/chenaniah-bot/audio_files && find $HOME/chenaniah-bot/audio_files -type f | wc -l | xargs echo "  Count:"
fi
echo ""

if [ -d "$HOME/projects/chenaniah/web/chenaniah-web" ]; then
    echo "Web directory:"
    du -sh $HOME/projects/chenaniah/web/chenaniah-web
fi
echo ""

echo "======================================"
echo "DONE - Copy this output"
echo "======================================"

