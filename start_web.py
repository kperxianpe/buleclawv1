#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_web.py - Blueclaw v1.0 Web Interface (Streamlit)

Usage:
    pip install streamlit
    streamlit run start_web.py
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

# Page config
st.set_page_config(
    page_title="Blueclaw v1.0",
    page_icon="🤖",
    layout="wide"
)

# Initialize
if 'coordinator' not in st.session_state:
    st.session_state.coordinator = create_coordinator_v3(use_real_execution=True)
    st.session_state.messages = []
    st.session_state.steps = []

st.title("🤖 Blueclaw v1.0 - AI Self-Operating Canvas")

# Sidebar
with st.sidebar:
    st.header("控制面板")
    
    if st.button("🆕 新任务"):
        st.session_state.messages = []
        st.session_state.steps = []
        st.rerun()
    
    st.divider()
    
    st.subheader("快速任务")
    if st.button("✈️ 规划旅行"):
        st.session_state.input_text = "我想规划一个周末短途旅行"
    if st.button("📁 列文件"):
        st.session_state.input_text = "列出当前目录的文件"
    if st.button("🐍 写代码"):
        st.session_state.input_text = "写一个Python计算斐波那契数列的函数"
    
    st.divider()
    
    st.subheader("执行状态")
    coord = st.session_state.coordinator
    st.write(f"状态: {coord.state.phase}")
    st.write(f"进度: {coord.state.progress}%")
    
    if st.button("⏸️ 暂停"):
        coord.execution_system.pause_execution()
        st.rerun()
    
    if st.button("▶️ 继续"):
        asyncio.run(coord.execution_system.resume_execution())
        st.rerun()

# Main layout
col1, col2 = st.columns([2, 3])

# Chat panel
with col1:
    st.subheader("💬 对话")
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Input
    user_input = st.chat_input("输入你的任务...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Create placeholders for AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # Setup coordinator to update UI
            coord = st.session_state.coordinator
            
            def on_message(msg):
                st.session_state.messages.append({"role": "assistant", "content": msg})
            
            def on_step_update(step_id, status, index):
                st.session_state.steps.append({
                    "step_id": step_id,
                    "status": status,
                    "index": index
                })
            
            coord.set_callbacks(
                on_message=on_message,
                on_step_update=on_step_update
            )
            
            # Run task
            response_placeholder.write("思考中...")
            asyncio.run(coord.start_task(user_input))
            
            response_placeholder.write("任务已启动，查看右侧面板")
        
        st.rerun()

# Canvas panel
with col2:
    st.subheader("📋 执行蓝图")
    
    if st.session_state.steps:
        for step in st.session_state.steps:
            status_icons = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }
            icon = status_icons.get(step["status"], "❓")
            st.write(f"{icon} 步骤 {step['index'] + 1}: {step['step_id']}")
    else:
        st.info("执行蓝图将在这里显示\n\n在左侧开始一个任务")

# Footer
st.divider()
st.caption("Blueclaw v1.0 - AI Self-Operating Canvas Framework")
