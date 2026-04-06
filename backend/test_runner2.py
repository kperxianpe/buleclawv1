#!/usr/bin/env python3
"""测试运行器 - 显示服务器输出"""
import subprocess
import sys
import time

# 启动服务器
print("Starting server...")
# 设置环境变量使用不同端口
import os
os.environ['PORT'] = '8765'
server = subprocess.Popen([sys.executable, "backend/main.py"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.STDOUT,
                         text=True)

# 等待服务器启动
time.sleep(3)

# 检查服务器是否还在运行
if server.poll() is not None:
    print("Server exited early!")
    output, _ = server.communicate()
    print("Server output:")
    print(output)
    sys.exit(1)

print("Server is running, running tests...")

# 运行测试
result = subprocess.run([sys.executable, "backend/tests/test_websocket.py"], 
                       capture_output=True, 
                       text=True)

print("Test stdout:")
print(result.stdout)
if result.stderr:
    print("Test stderr:")
    print(result.stderr)

# 停止服务器
server.terminate()
try:
    server.wait(timeout=5)
except:
    server.kill()

# 获取服务器输出
stdout, _ = server.communicate()
if stdout:
    print("\nServer output:")
    print(stdout)

sys.exit(result.returncode)
