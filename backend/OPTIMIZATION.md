# Week 18.5 - Backend Optimization Guide

## 1. Performance Benchmarks

### Current Performance (Baseline)

| Metric | Target | Current |
|--------|--------|---------|
| Connection establishment | < 100ms | TBD |
| Task creation latency | < 50ms | TBD |
| Message round-trip | < 20ms | TBD |
| Concurrent connections | > 100 | TBD |
| Messages/sec | > 1000 | TBD |

## 2. Optimization Areas

### 2.1 WebSocket Connection Pool

**Problem**: Creating new connections for each request is expensive.

**Solution**: Implement connection pooling for internal services.

```python
# backend/websocket/pool.py
class ConnectionPool:
    """WebSocket 连接池"""
    
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.connections = asyncio.Queue(maxsize=max_size)
        self.active = 0
    
    async def acquire(self):
        if not self.connections.empty():
            return await self.connections.get()
        
        if self.active < self.max_size:
            self.active += 1
            return await websockets.connect(URI)
        
        # Wait for available connection
        return await self.connections.get()
    
    async def release(self, conn):
        await self.connections.put(conn)
```

### 2.2 Message Queue

**Problem**: Synchronous message processing blocks other clients.

**Solution**: Implement async message queue with worker pool.

```python
# backend/core/message_queue.py
class MessageQueue:
    """异步消息队列"""
    
    def __init__(self, num_workers=4):
        self.queue = asyncio.Queue()
        self.workers = []
        self.num_workers = num_workers
    
    async def start(self):
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)
    
    async def _worker(self, worker_id):
        while True:
            message, websocket = await self.queue.get()
            try:
                await self.process_message(message, websocket)
            finally:
                self.queue.task_done()
    
    async def enqueue(self, message, websocket):
        await self.queue.put((message, websocket))
```

### 2.3 Checkpoint Optimization

**Problem**: Saving checkpoints on every update is I/O intensive.

**Solution**: Batch checkpoint writes and compress data.

```python
# backend/core/checkpoint_optimized.py
class OptimizedCheckpointManager:
    """优化的检查点管理器"""
    
    def __init__(self, storage_dir="./checkpoints", batch_interval=5):
        self.storage_dir = storage_dir
        self.batch_interval = batch_interval
        self.pending = {}
        self.last_save = time.time()
        
        # Start background batch writer
        asyncio.create_task(self._batch_writer())
    
    async def save_checkpoint(self, task):
        """非阻塞保存检查点"""
        self.pending[task.id] = task
        
        # 立即保存关键状态
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            await self._flush_one(task.id)
    
    async def _batch_writer(self):
        """后台批量写入"""
        while True:
            await asyncio.sleep(self.batch_interval)
            
            if self.pending:
                await self._flush_all()
    
    async def _flush_all(self):
        """批量写入所有待保存的检查点"""
        tasks = list(self.pending.items())
        self.pending = {}
        
        for task_id, task in tasks:
            await self._write_to_disk(task)
    
    async def _write_to_disk(self, task):
        """写入磁盘（压缩）"""
        import gzip
        import json
        
        data = json.dumps({"task": task.to_dict()})
        compressed = gzip.compress(data.encode())
        
        filepath = os.path.join(self.storage_dir, f"{task.id}.json.gz")
        with open(filepath, 'wb') as f:
            f.write(compressed)
```

### 2.4 JSON Serialization

**Problem**: Standard json module is slow for large payloads.

**Solution**: Use orjson or ujson for faster serialization.

```python
# requirements.txt
orjson>=3.8.0

# backend/utils/json.py
try:
    import orjson as json
    
    def json_dumps(obj):
        return json.dumps(obj).decode()
    
    def json_loads(s):
        return json.loads(s)
        
except ImportError:
    import json
    
    def json_dumps(obj):
        return json.dumps(obj, ensure_ascii=False)
    
    def json_loads(s):
        return json.loads(s)
```

### 2.5 Memory Management

**Problem**: Task objects accumulate in memory.

**Solution**: Implement LRU cache and periodic cleanup.

```python
# backend/core/task_manager_optimized.py
from functools import lru_cache
import weakref

class OptimizedTaskManager:
    """优化的任务管理器"""
    
    def __init__(self, max_active_tasks=1000, ttl=3600):
        self.max_active_tasks = max_active_tasks
        self.ttl = ttl
        
        # Active tasks in memory
        self.active_tasks = {}
        
        # Completed tasks stored as weak references
        self.completed_tasks = weakref.WeakValueDictionary()
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """定期清理过期任务"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            
            now = time.time()
            expired = [
                task_id for task_id, task in self.active_tasks.items()
                if now - task.updated_at > self.ttl
                and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            
            for task_id in expired:
                # Move to weak reference
                self.completed_tasks[task_id] = self.active_tasks[task_id]
                del self.active_tasks[task_id]
            
            print(f"Cleaned up {len(expired)} expired tasks")
```

## 3. Configuration Tuning

### 3.1 WebSocket Server Settings

```python
# backend/config/server.py
SERVER_CONFIG = {
    # Connection settings
    'ping_interval': 20,        # Keep-alive ping interval (seconds)
    'ping_timeout': 10,         # Ping timeout (seconds)
    'close_timeout': 10,        # Close handshake timeout (seconds)
    'max_size': 10 * 1024 * 1024,  # Max message size (10MB)
    'max_queue': 32,            # Max queued messages per connection
    
    # Performance settings
    'compression': True,        # Enable compression
    'origins': None,            # Allowed origins (None = all)
    'extensions': None,         # WebSocket extensions
}
```

### 3.2 Task Manager Settings

```python
# backend/config/task.py
TASK_CONFIG = {
    # Limits
    'max_concurrent_tasks': 100,
    'max_tasks_per_connection': 10,
    'max_task_duration': 3600,  # 1 hour
    
    # Timing
    'checkpoint_interval': 30,   # Seconds between checkpoints
    'cleanup_interval': 300,     # 5 minutes
    'task_ttl': 86400,          # 24 hours
    
    # Retry settings
    'max_retries': 3,
    'retry_delay': 1.0,         # Seconds
}
```

## 4. Monitoring

### 4.1 Metrics Collection

```python
# backend/monitoring/metrics.py
import time
from collections import defaultdict

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}
    
    def increment(self, name, value=1):
        """计数器增加"""
        self.counters[name] += value
    
    def timer(self, name, duration):
        """记录耗时"""
        self.timers[name].append(duration)
        # Keep only last 1000 samples
        if len(self.timers[name]) > 1000:
            self.timers[name] = self.timers[name][-1000:]
    
    def gauge(self, name, value):
        """设置仪表盘值"""
        self.gauges[name] = value
    
    def report(self):
        """生成报告"""
        report = {
            'counters': dict(self.counters),
            'timers': {
                name: {
                    'count': len(times),
                    'avg': sum(times) / len(times) if times else 0,
                    'min': min(times) if times else 0,
                    'max': max(times) if times else 0,
                }
                for name, times in self.timers.items()
            },
            'gauges': self.gauges
        }
        return report

# Global metrics instance
metrics = MetricsCollector()
```

### 4.2 Health Check Endpoint

```python
# backend/monitoring/health.py
async def health_check():
    """健康检查"""
    checks = {
        'websocket_server': check_websocket_server(),
        'task_manager': check_task_manager(),
        'checkpoint_storage': check_storage(),
        'memory_usage': check_memory(),
    }
    
    results = await asyncio.gather(*checks.values(), return_exceptions=True)
    
    status = {
        name: 'ok' if not isinstance(result, Exception) else 'error'
        for name, result in zip(checks.keys(), results)
    }
    
    all_ok = all(s == 'ok' for s in status.values())
    
    return {
        'status': 'healthy' if all_ok else 'unhealthy',
        'checks': status,
        'timestamp': time.time()
    }
```

## 5. Deployment Optimization

### 5.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with optimizations
CMD ["python", "-O", "main.py"]
```

### 5.2 Process Management

```ini
# supervisord.conf
[program:blueclaw]
command=python -O main.py
directory=/app
autostart=true
autorestart=true
numprocs=4          # Run 4 worker processes
process_name=%(program_name)s_%(process_num)02d
```

## 6. Testing Optimizations

### 6.1 Run All Tests

```bash
# Complete test suite
cd backend

# Unit tests
python -m pytest tests/integration/ -v

# Performance tests
python tests/performance/test_latency.py

# Stress tests
python tests/stress/test_load.py

# All tests
python -m pytest tests/ -v --tb=short
```

### 6.2 Profiling

```bash
# CPU profiling
python -m cProfile -o profile.stats main.py

# Memory profiling
python -m memory_profiler main.py

# Line profiling
kernprof -l -v main.py
```

## 7. Checklist

### Before Production

- [ ] Run complete test suite (all tests pass)
- [ ] Verify performance benchmarks met
- [ ] Load testing at 2x expected traffic
- [ ] Memory leak test (24 hours)
- [ ] Security audit
- [ ] Monitoring dashboards setup
- [ ] Alerting rules configured
- [ ] Backup and recovery tested
- [ ] Documentation complete
- [ ] Rollback plan ready

---

*Week 18.5 Optimization Guide*
