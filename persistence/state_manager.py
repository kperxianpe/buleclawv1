#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state_manager.py - Blueclaw v1.0 State Persistence Manager

状态持久化管理器 - 任务状态可保存恢复
支持 SQLite 存储、任务历史、崩溃恢复
"""

import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import os


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    THINKING = "thinking"
    WAITING_INPUT = "waiting_input"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class TaskSummary:
    """任务摘要"""
    id: str
    user_input: str
    status: str
    updated_at: str
    intent: str = ""
    progress: int = 0


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    task_id: str
    phase: str
    data: Dict[str, Any]
    created_at: str


class StatePersistenceManager:
    """
    状态持久化管理器
    
    功能：
    - 任务状态保存/加载
    - 执行检查点
    - 崩溃后恢复
    - 任务历史查询
    """
    
    def __init__(self, db_path: str = "blueclaw_v1.db"):
        """
        初始化状态管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    user_input TEXT NOT NULL,
                    intent TEXT,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    thinking_blueprint TEXT,
                    execution_blueprint TEXT,
                    current_step_id TEXT,
                    execution_mode TEXT DEFAULT 'real',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # 检查点表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            
            # 执行历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            
            # 用户偏好表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_task ON checkpoints(task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_task ON execution_history(task_id)
            """)
            
            conn.commit()
    
    def save_task(self, task: Dict[str, Any]) -> str:
        """
        保存任务状态
        
        Args:
            task: 任务数据字典
            
        Returns:
            任务 ID
        """
        task_id = task.get('id') or str(uuid.uuid4())
        
        # 序列化复杂对象
        thinking_blueprint = json.dumps(task.get('thinking_blueprint', {}), ensure_ascii=False)
        execution_blueprint = json.dumps(task.get('execution_blueprint', {}), ensure_ascii=False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, user_input, intent, status, progress, thinking_blueprint, 
                 execution_blueprint, current_step_id, execution_mode, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task.get('user_input', ''),
                task.get('intent', ''),
                task.get('status', 'pending'),
                task.get('progress', 0),
                thinking_blueprint,
                execution_blueprint,
                task.get('current_step_id', ''),
                task.get('execution_mode', 'real'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            
        return task_id
    
    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        加载任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务数据字典，如果不存在返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM tasks WHERE id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # 获取列名
            columns = [description[0] for description in cursor.description]
            
            # 构建字典
            task = dict(zip(columns, row))
            
            # 反序列化 JSON 字段
            try:
                task['thinking_blueprint'] = json.loads(task.get('thinking_blueprint', '{}') or '{}')
            except:
                task['thinking_blueprint'] = {}
                
            try:
                task['execution_blueprint'] = json.loads(task.get('execution_blueprint', '{}') or '{}')
            except:
                task['execution_blueprint'] = {}
                
            return task
    
    def create_checkpoint(self, task_id: str, phase: str, 
                          data: Dict[str, Any]) -> str:
        """
        创建检查点
        
        Args:
            task_id: 任务 ID
            phase: 阶段（thinking/executing/etc）
            data: 检查点数据
            
        Returns:
            检查点 ID
        """
        checkpoint_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO checkpoints (checkpoint_id, task_id, phase, data)
                VALUES (?, ?, ?, ?)
            """, (
                checkpoint_id,
                task_id,
                phase,
                json.dumps(data, ensure_ascii=False)
            ))
            
            conn.commit()
            
        return checkpoint_id
    
    def get_latest_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """
        获取最新检查点
        
        Args:
            task_id: 任务 ID
            
        Returns:
            最新检查点，如果没有返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT checkpoint_id, task_id, phase, data, created_at
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (task_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return Checkpoint(
                checkpoint_id=row[0],
                task_id=row[1],
                phase=row[2],
                data=json.loads(row[3]),
                created_at=row[4]
            )
    
    def list_checkpoints(self, task_id: str, limit: int = 10) -> List[Checkpoint]:
        """
        列出任务检查点
        
        Args:
            task_id: 任务 ID
            limit: 数量限制
            
        Returns:
            检查点列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT checkpoint_id, task_id, phase, data, created_at
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (task_id, limit))
            
            checkpoints = []
            for row in cursor.fetchall():
                checkpoints.append(Checkpoint(
                    checkpoint_id=row[0],
                    task_id=row[1],
                    phase=row[2],
                    data=json.loads(row[3]),
                    created_at=row[4]
                ))
                
            return checkpoints
    
    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        从检查点恢复
        
        Args:
            checkpoint_id: 检查点 ID
            
        Returns:
            恢复的数据
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, phase, data FROM checkpoints
                WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            task_id, phase, data_json = row
            
            # 同时加载任务基础信息
            task = self.load_task(task_id)
            
            checkpoint_data = json.loads(data_json)
            checkpoint_data['task_id'] = task_id
            checkpoint_data['phase'] = phase
            checkpoint_data['task'] = task
            
            return checkpoint_data
    
    def list_recent_tasks(self, limit: int = 10) -> List[TaskSummary]:
        """
        获取最近任务列表
        
        Args:
            limit: 数量限制
            
        Returns:
            任务摘要列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_input, status, updated_at, intent, progress
                FROM tasks
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append(TaskSummary(
                    id=row[0],
                    user_input=row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                    status=row[2],
                    updated_at=row[3],
                    intent=row[4] or "",
                    progress=row[5] or 0
                ))
                
            return tasks
    
    def get_tasks_by_status(self, status: TaskStatus, limit: int = 10) -> List[TaskSummary]:
        """
        按状态获取任务
        
        Args:
            status: 任务状态
            limit: 数量限制
            
        Returns:
            任务摘要列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_input, status, updated_at, intent, progress
                FROM tasks
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (status.value, limit))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append(TaskSummary(
                    id=row[0],
                    user_input=row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                    status=row[2],
                    updated_at=row[3],
                    intent=row[4] or "",
                    progress=row[5] or 0
                ))
                
            return tasks
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                           progress: Optional[int] = None):
        """
        更新任务状态
        
        Args:
            task_id: 任务 ID
            status: 新状态
            progress: 进度（可选）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if progress is not None:
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, progress = ?, updated_at = ?
                    WHERE id = ?
                """, (status.value, progress, datetime.now().isoformat(), task_id))
            else:
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (status.value, datetime.now().isoformat(), task_id))
                
            # 如果完成，记录完成时间
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.ABORTED]:
                cursor.execute("""
                    UPDATE tasks SET completed_at = ? WHERE id = ?
                """, (datetime.now().isoformat(), task_id))
                
            conn.commit()
    
    def delete_task(self, task_id: str):
        """
        删除任务
        
        Args:
            task_id: 任务 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
    
    def get_recovery_candidates(self) -> List[TaskSummary]:
        """
        获取可恢复的任务（执行中或暂停的任务）
        
        Returns:
            可恢复任务列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_input, status, updated_at, intent, progress
                FROM tasks
                WHERE status IN ('executing', 'paused', 'waiting_input')
                ORDER BY updated_at DESC
            """)
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append(TaskSummary(
                    id=row[0],
                    user_input=row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                    status=row[2],
                    updated_at=row[3],
                    intent=row[4] or "",
                    progress=row[5] or 0
                ))
                
            return tasks
    
    def set_preference(self, key: str, value: Any):
        """
        设置用户偏好
        
        Args:
            key: 偏好键
            value: 偏好值
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now().isoformat()))
            
            conn.commit()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取用户偏好
        
        Args:
            key: 偏好键
            default: 默认值
            
        Returns:
            偏好值
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM user_preferences WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return default
    
    def cleanup_old_tasks(self, days: int = 30):
        """
        清理旧任务
        
        Args:
            days: 保留天数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM tasks
                WHERE updated_at < datetime('now', '-{} days')
                AND status IN ('completed', 'failed', 'aborted')
            """.format(days))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总任务数
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]
            
            # 状态分布
            cursor.execute("""
                SELECT status, COUNT(*) FROM tasks GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # 今日任务
            cursor.execute("""
                SELECT COUNT(*) FROM tasks
                WHERE date(created_at) = date('now')
            """)
            today_tasks = cursor.fetchone()[0]
            
            # 数据库大小
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                "total_tasks": total_tasks,
                "status_distribution": status_counts,
                "today_tasks": today_tasks,
                "database_size_bytes": db_size,
                "database_path": self.db_path
            }


# 便捷函数
def create_state_manager(db_path: str = "blueclaw_v1.db") -> StatePersistenceManager:
    """创建状态管理器"""
    return StatePersistenceManager(db_path)


def generate_task_id() -> str:
    """生成任务 ID"""
    return str(uuid.uuid4())
