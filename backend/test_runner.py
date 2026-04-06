#!/usr/bin/env python3
"""测试运行器"""
import subprocess
import sys
import time

# 启动服务器
print("Starting server...")
server = subprocess.Popen([sys.executable, "backend/main.py"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)

# 等待服务器启动
time.sleep(3)

# 运行测试
print("Running tests...")
result = subprocess.run([sys.executable, "backend/tests/test_websocket.py"], 
                       capture_output=True, 
                       text=True)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# 停止服务器
server.terminate()
server.wait(timeout=5)

sys.exit(result.returncode)
