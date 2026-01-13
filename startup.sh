#!/bin/bash
echo "容器启动，等待2秒..."
sleep 2
echo "开始启动应用..."
exec python bot.py
