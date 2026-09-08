@echo off
echo Starting Solana Memecoin Tracker Frontend (Vue 3 + Vite)...
cd /d %~dp0frontend
call npm install
npm run dev
