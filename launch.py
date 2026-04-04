#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launch.py - Blueclaw v1.0 Launcher

Usage:
    python launch.py --mode console
    python launch.py --mode test
    python launch.py --task "List files in current directory"
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add blueclaw to path
sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3


async def console_mode():
    """Interactive console mode"""
    print("\n" + "="*60)
    print("Blueclaw v1.0 - Console Mode")
    print("="*60)
    print("\nCommands:")
    print("  /quit    - Exit")
    print("  /skills  - List available skills")
    print("  /status  - Show current status")
    print("  /help    - Show this help")
    print("\nEnter your task below:")
    print("-"*60)
    
    coord = create_coordinator_v3(use_real_execution=True)
    
    def on_message(msg):
        print(f"  {msg}")
    
    def on_step_update(step_id, status, index):
        icon = "OK" if status == "completed" else ("RUN" if status == "running" else "--")
        print(f"  Step {index + 1}: [{icon}] {step_id}")
    
    def on_execution_complete(result):
        print(f"\n  [DONE] {result.get('summary', 'Completed')}")
    
    coord.set_callbacks(
        on_message=on_message,
        on_step_update=on_step_update,
        on_execution_complete=on_execution_complete
    )
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("Goodbye!")
                break
            
            if user_input == "/skills":
                skills = coord.list_skills()
                print(f"\nAvailable skills: {', '.join(skills)}")
                continue
            
            if user_input == "/status":
                progress = coord.get_progress()
                print(f"\nStatus: {coord.state.phase}")
                print(f"Progress: {progress.get('percentage', 0)}%")
                continue
            
            if user_input == "/help":
                print("\nCommands: /quit, /skills, /status, /help")
                continue
            
            if user_input.startswith("/"):
                print(f"Unknown command: {user_input}")
                continue
            
            # Start task
            await coord.start_task(user_input)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def run_task(task: str):
    """Run a single task"""
    print(f"\n[Task] {task}")
    print("-"*60)
    
    coord = create_coordinator_v3(use_real_execution=True)
    
    messages = []
    steps = []
    
    def on_message(msg):
        messages.append(msg)
        print(f"  {msg}")
    
    def on_step_update(step_id, status, index):
        steps.append((step_id, status, index))
        icon = "OK" if status == "completed" else ("RUN" if status == "running" else "--")
        print(f"  Step {index + 1}: [{icon}] {step_id}")
    
    def on_execution_complete(result):
        print(f"\n  [DONE] {result.get('summary', 'Completed')}")
    
    def on_question(question):
        print(f"\n  [QUESTION] {question.text}")
        if question.options:
            for opt in question.options:
                print(f"    [{opt['id']}] {opt['label']}: {opt['description']}")
    
    def on_options(options):
        print(f"\n  [OPTIONS] Select one:")
        for opt in options:
            default = " (default)" if opt.is_default else ""
            print(f"    [{opt.id}] {opt.label}{default}")
            print(f"        {opt.description}")
    
    coord.set_callbacks(
        on_message=on_message,
        on_step_update=on_step_update,
        on_execution_complete=on_execution_complete,
        on_question=on_question,
        on_options=on_options
    )
    
    await coord.start_task(task)
    
    return {
        "messages": messages,
        "steps": steps,
        "state": coord.state
    }


def main():
    parser = argparse.ArgumentParser(description="Blueclaw v1.0 Launcher")
    parser.add_argument("--mode", choices=["console", "test"], default="console",
                       help="Launch mode")
    parser.add_argument("--task", type=str, help="Single task to execute")
    
    args = parser.parse_args()
    
    if args.task:
        result = asyncio.run(run_task(args.task))
    elif args.mode == "console":
        asyncio.run(console_mode())
    elif args.mode == "test":
        print("Run: python -m pytest tests/")


if __name__ == "__main__":
    main()
