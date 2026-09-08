#!/usr/bin/env bash
# 停止后端与前端进程
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "已停止后端" || echo "后端未运行"
pkill -f "vite" 2>/dev/null && echo "已停止前端" || echo "前端未运行"
