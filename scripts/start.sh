#!/usr/bin/env bash
# 一键启动：后端 8000 + 前端 5173
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"

echo "==> 启动后端 FastAPI (http://127.0.0.1:8000/docs)"
cd "$ROOT/server"
if [ ! -d ".venv" ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT/server/backend.log" 2>&1 &

echo "==> 启动前端 Vue (http://localhost:5173)"
cd "$ROOT/web"
if [ ! -d "node_modules" ]; then
  npm install
fi
nohup npm run dev > "$ROOT/web/frontend.log" 2>&1 &

sleep 3
echo "完成：后端 http://127.0.0.1:8000/docs  前端 http://localhost:5173"
echo "默认管理员：admin / admin123"
