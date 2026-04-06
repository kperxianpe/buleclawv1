#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 18.5 - Complete Test Suite Runner

Runs all integration, performance and stress tests.
"""

import subprocess
import sys
import os
import time

# 配置
TEST_CONFIG = {
    'server_startup_delay': 3,
    'server_port': 8765,
    'tests': [
        {
            'name': 'Integration Tests',
            'script': 'backend/tests/integration/test_api_complete.py',
            'timeout': 120
        },
        {
            'name': 'Performance Tests',
            'script': 'backend/tests/performance/test_latency.py',
            'timeout': 60
        },
        {
            'name': 'Stress Tests',
            'script': 'backend/tests/stress/test_load.py',
            'timeout': 120
        }
    ]
}


def start_server():
    """启动后端服务器"""
    print("Starting backend server...")
    env = os.environ.copy()
    env['PORT'] = str(TEST_CONFIG['server_port'])
    
    proc = subprocess.Popen(
        [sys.executable, 'backend/main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    # 等待服务器启动
    time.sleep(TEST_CONFIG['server_startup_delay'])
    
    # 检查服务器是否还在运行
    if proc.poll() is not None:
        print("Server failed to start!")
        output, _ = proc.communicate()
        print(output.decode())
        return None
    
    print(f"Server started on port {TEST_CONFIG['server_port']}")
    return proc


def stop_server(proc):
    """停止后端服务器"""
    if proc is None:
        return
    
    print("\nStopping server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
        proc.wait()
    print("Server stopped")


def run_test(test_config):
    """运行单个测试"""
    print(f"\n{'='*70}")
    print(f"Running: {test_config['name']}")
    print(f"{'='*70}")
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_config['script']],
            capture_output=True,
            text=True,
            timeout=test_config['timeout']
        )
        
        elapsed = time.time() - start
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        print(f"\n{test_config['name']}: {'PASS' if success else 'FAIL'} ({elapsed:.1f}s)")
        
        return {
            'name': test_config['name'],
            'success': success,
            'elapsed': elapsed,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"\n{test_config['name']}: TIMEOUT")
        return {
            'name': test_config['name'],
            'success': False,
            'elapsed': test_config['timeout'],
            'error': 'timeout'
        }
    except Exception as e:
        print(f"\n{test_config['name']}: ERROR - {e}")
        return {
            'name': test_config['name'],
            'success': False,
            'elapsed': 0,
            'error': str(e)
        }


def print_summary(results):
    """打印测试摘要"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for r in results:
        status = "PASS" if r['success'] else "FAIL"
        elapsed = r.get('elapsed', 0)
        print(f"{r['name']:<30} {status:>6} ({elapsed:.1f}s)")
    
    print("-"*70)
    print(f"Total: {passed}/{total} test suites passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    return passed == total


def main():
    """主函数"""
    print("="*70)
    print("Week 18.5 - Complete Test Suite")
    print("="*70)
    
    # 启动服务器
    server = start_server()
    if server is None:
        return 1
    
    results = []
    
    try:
        # 运行所有测试
        for test in TEST_CONFIG['tests']:
            result = run_test(test)
            results.append(result)
    finally:
        # 确保服务器停止
        stop_server(server)
    
    # 打印摘要
    all_passed = print_summary(results)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
