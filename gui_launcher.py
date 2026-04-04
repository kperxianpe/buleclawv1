#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_launcher.py - Blueclaw v1.0 GUI Launcher (tkinter version)

Features:
- Three-panel layout (Chat | Canvas | Log)
- Dynamic thinking display
- Execution blueprint visualization
- Real-time step updates
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import threading
from pathlib import Path
import sys

# Add blueclaw to path
sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3


class BlueclawGUI:
    """Blueclaw v1.0 GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Blueclaw v1.0 - AI Self-Operating Canvas")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Initialize coordinator
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Create UI
        self.create_menu()
        self.create_main_layout()
        self.create_status_bar()
        
        # Welcome message
        self.add_chat_message("system", "Blueclaw v1.0 已启动")
        self.add_chat_message("ai", "你好！我是Blueclaw，你的AI助手。\n\n我可以帮你：\n• 规划旅行\n• 编写代码\n• 分析数据\n• 执行文件操作\n\n请告诉我你想做什么？")
    
    def setup_callbacks(self):
        """Setup coordinator callbacks"""
        self.coordinator.set_callbacks(
            on_state_change=self.on_state_change,
            on_message=self.on_message,
            on_execution_preview=self.on_execution_preview,
            on_question=self.on_question,
            on_options=self.on_options,
            on_blueprint_loaded=self.on_blueprint_loaded,
            on_step_update=self.on_step_update,
            on_execution_complete=self.on_execution_complete,
            on_intervention_needed=self.on_intervention_needed
        )
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建任务", command=self.clear_chat)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="清除日志", command=self.clear_log)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_main_layout(self):
        """Create three-panel layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=3)  # Chat panel
        main_frame.columnconfigure(1, weight=5)  # Canvas panel
        main_frame.columnconfigure(2, weight=2)  # Log panel
        main_frame.rowconfigure(0, weight=1)
        
        # === Panel 1: Chat (30%) ===
        self.create_chat_panel(main_frame, 0)
        
        # === Panel 2: Canvas (50%) ===
        self.create_canvas_panel(main_frame, 1)
        
        # === Panel 3: Log (20%) ===
        self.create_log_panel(main_frame, 2)
    
    def create_chat_panel(self, parent, column):
        """Create chat panel"""
        frame = ttk.LabelFrame(parent, text="对话", padding=5)
        frame.grid(row=0, column=column, sticky="nsew", padx=2, pady=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.rowconfigure(2, weight=0)
        
        # Chat history
        self.chat_text = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, state=tk.DISABLED,
            font=("Microsoft YaHei", 10)
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        
        # Input frame
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, font=("Microsoft YaHei", 10))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.input_entry.bind("<Return>", self.on_send)
        
        send_btn = ttk.Button(input_frame, text="发送", command=self.on_send)
        send_btn.grid(row=0, column=1)
        
        # Quick actions
        quick_frame = ttk.Frame(frame)
        quick_frame.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(quick_frame, text="规划旅行", 
                  command=lambda: self.quick_task("我想规划一个周末短途旅行")).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="列文件", 
                  command=lambda: self.quick_task("列出当前目录的文件")).pack(side=tk.LEFT, padx=2)
    
    def create_canvas_panel(self, parent, column):
        """Create canvas panel (execution blueprint visualization)"""
        frame = ttk.LabelFrame(parent, text="执行蓝图", padding=5)
        frame.grid(row=0, column=column, sticky="nsew", padx=2, pady=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Canvas for visualization
        self.canvas = tk.Canvas(frame, bg="#f5f5f5", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Canvas content frame
        self.canvas_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
        
        self.canvas_frame.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Initial message
        self.canvas_label = ttk.Label(
            self.canvas_frame, 
            text="执行蓝图将在这里显示\n\n开始一个任务来查看执行流程",
            justify=tk.CENTER,
            font=("Microsoft YaHei", 12)
        )
        self.canvas_label.pack(expand=True, pady=100)
        
        # Step frames storage
        self.step_frames = {}
    
    def create_log_panel(self, parent, column):
        """Create log panel"""
        frame = ttk.LabelFrame(parent, text="日志", padding=5)
        frame.grid(row=0, column=column, sticky="nsew", padx=2, pady=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 9), height=10
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Action buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Button(btn_frame, text="暂停", command=self.pause_execution).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="继续", command=self.resume_execution).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="重置", command=self.clear_canvas).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Label(
            self.root, 
            text="就绪 | 模式: 真实执行",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # === Event Handlers ===
    
    def on_send(self, event=None):
        """Handle send button"""
        text = self.input_entry.get().strip()
        if not text:
            return
        
        self.input_entry.delete(0, tk.END)
        self.add_chat_message("user", text)
        
        # Run task in background
        threading.Thread(target=self.run_task_async, args=(text,), daemon=True).start()
    
    def quick_task(self, task):
        """Quick task button"""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, task)
        self.on_send()
    
    def run_task_async(self, task):
        """Run task asynchronously"""
        asyncio.run(self.coordinator.start_task(task))
    
    def add_chat_message(self, role, text):
        """Add message to chat"""
        self.chat_text.configure(state=tk.NORMAL)
        
        if role == "user":
            self.chat_text.insert(tk.END, f"\n你: {text}\n", "user")
            self.chat_text.tag_config("user", foreground="#0066cc", font=("Microsoft YaHei", 10, "bold"))
        elif role == "ai":
            self.chat_text.insert(tk.END, f"\nAI: {text}\n", "ai")
            self.chat_text.tag_config("ai", foreground="#333333", font=("Microsoft YaHei", 10))
        elif role == "system":
            self.chat_text.insert(tk.END, f"\n[系统] {text}\n", "system")
            self.chat_text.tag_config("system", foreground="#666666", font=("Microsoft YaHei", 9))
        
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.see(tk.END)
    
    # === Callback Handlers ===
    
    def on_state_change(self, state):
        """Handle state change"""
        self.root.after(0, lambda: self.status_bar.configure(
            text=f"状态: {state.phase} | 进度: {state.progress}% | 模式: {state.execution_mode}"
        ))
    
    def on_message(self, msg):
        """Handle log message"""
        self.root.after(0, lambda: self.add_log(msg))
    
    def add_log(self, msg):
        """Add log message"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def on_execution_preview(self, preview):
        """Handle execution preview"""
        def update():
            self.clear_canvas()
            self.add_chat_message("ai", f"执行计划已生成：\n\n任务类型: {preview.get('task_type', 'unknown')}\n复杂度: {preview.get('complexity', 'medium')}\n预计时间: {preview.get('estimated_time', 'unknown')}\n\n步骤:\n" + 
                "\n".join([f"  {i+1}. {step.get('name', '未命名')}" 
                         for i, step in enumerate(preview.get('steps', []))]))
        self.root.after(0, update)
    
    def on_question(self, question):
        """Handle clarification question"""
        def update():
            text = f"{question.text}\n\n"
            if question.options:
                for opt in question.options:
                    text += f"[{opt['id']}] {opt['label']}: {opt['description']}\n"
            self.add_chat_message("ai", text)
        self.root.after(0, update)
    
    def on_options(self, options):
        """Handle options"""
        def update():
            text = "请选择执行方案:\n\n"
            for opt in options:
                default = " (推荐)" if opt.is_default else ""
                text += f"[{opt.id}] {opt.label}{default}\n    {opt.description}\n\n"
            self.add_chat_message("ai", text)
        self.root.after(0, update)
    
    def on_blueprint_loaded(self, steps):
        """Handle blueprint loaded"""
        def update():
            self.clear_canvas()
            for i, step in enumerate(steps):
                self.create_step_widget(i, step.name, step.description)
        self.root.after(0, update)
    
    def on_step_update(self, step_id, status, index):
        """Handle step update"""
        def update():
            if step_id in self.step_frames:
                self.update_step_status(step_id, status)
        self.root.after(0, update)
    
    def on_execution_complete(self, result):
        """Handle execution complete"""
        def update():
            summary = result.get('summary', '执行完成')
            self.add_chat_message("ai", f"✅ {summary}")
            messagebox.showinfo("执行完成", summary)
        self.root.after(0, update)
    
    def on_intervention_needed(self, step_id, reason):
        """Handle intervention needed"""
        def update():
            self.add_chat_message("system", f"需要干预: {reason}")
            if messagebox.askyesno("干预", f"{reason}\n\n是否回退到思考阶段？"):
                threading.Thread(
                    target=lambda: asyncio.run(self.coordinator.handle_intervention("replan")),
                    daemon=True
                ).start()
        self.root.after(0, update)
    
    # === Canvas Widgets ===
    
    def create_step_widget(self, index, name, description):
        """Create a step widget in canvas"""
        frame = ttk.Frame(self.canvas_frame, relief=tk.RIDGE, borderwidth=1, padding=10)
        frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Status icon
        icon_label = ttk.Label(frame, text="⏳", font=("Segoe UI Emoji", 16))
        icon_label.pack(side=tk.LEFT, padx=5)
        
        # Content
        content_frame = ttk.Frame(frame)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(content_frame, text=f"步骤 {index + 1}: {name}", 
                 font=("Microsoft YaHei", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(content_frame, text=description, 
                 font=("Microsoft YaHei", 9), foreground="#666").pack(anchor=tk.W)
        
        # Store reference
        self.step_frames[f"step_{index}"] = {
            "frame": frame,
            "icon": icon_label
        }
    
    def update_step_status(self, step_id, status):
        """Update step status icon"""
        if step_id not in self.step_frames:
            return
        
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️",
            "skipped": "⏭️"
        }
        
        icon = icons.get(status, "❓")
        self.step_frames[step_id]["icon"].configure(text=icon)
        
        # Highlight running step
        if status == "running":
            self.step_frames[step_id]["frame"].configure(style="Running.TFrame")
    
    def clear_canvas(self):
        """Clear canvas"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.step_frames.clear()
        
        self.canvas_label = ttk.Label(
            self.canvas_frame, 
            text="执行蓝图将在这里显示\n\n开始一个任务来查看执行流程",
            justify=tk.CENTER,
            font=("Microsoft YaHei", 12)
        )
        self.canvas_label.pack(expand=True, pady=100)
    
    def clear_chat(self):
        """Clear chat"""
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.configure(state=tk.DISABLED)
        self.add_chat_message("system", "新任务已开始")
    
    def clear_log(self):
        """Clear log"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def pause_execution(self):
        """Pause execution"""
        self.coordinator.execution_system.pause_execution()
        self.add_chat_message("system", "执行已暂停")
    
    def resume_execution(self):
        """Resume execution"""
        threading.Thread(
            target=lambda: asyncio.run(self.coordinator.execution_system.resume_execution()),
            daemon=True
        ).start()
        self.add_chat_message("system", "执行已继续")
    
    def on_canvas_configure(self, event=None):
        """Configure canvas scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "关于 Blueclaw v1.0",
            "Blueclaw v1.0\n\nAI Self-Operating Canvas Framework\n\n功能:\n• 动态思考引擎\n• 执行蓝图可视化\n• 真实 Skill 执行\n• 干预机制"
        )


def main():
    """Main entry"""
    root = tk.Tk()
    app = BlueclawGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
