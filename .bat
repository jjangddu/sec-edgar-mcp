@echo off
chcp 65001 > nul
cd /d "C:\mcp\pythonProject"

:: [핵심] fastmcp를 실행하되, 로고를 끄는 옵션(--no-banner)을 추가했습니다.
"C:\Users\장동우\AppData\Local\Programs\Python\Python311\Scripts\fastmcp.exe" run main.py --no-banner