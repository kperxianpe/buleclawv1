# Blueclaw v1.0

AI Self-Operating Canvas Framework with Real Execution Capabilities

## Features

- **Dynamic Thinking Engine**: 80% scenarios with 0-1 selection
- **Execution Blueprint System**: Visual, interruptible execution flow
- **Real Skill Execution**: File, Shell, Code, Search, Browser skills
- **Memory System**: Working and long-term memory
- **Intervention Support**: Pause, REPLAN, skip, retry

## Quick Start

### GUI Mode (Recommended)

```bash
# Option 1: Native GUI (tkinter)
python start_gui.py

# Option 2: Web Interface (Streamlit)
pip install streamlit
streamlit run start_web.py
```

### Console Mode

```bash
python launch.py --mode console
```

### Run Single Task

```bash
python launch.py --task "List files in current directory"
```

### Run Tests

```bash
python tests/test_integration.py
```

## Programmatic Usage

```python
import asyncio
from blueclaw import create_coordinator_v3

async def main():
    # Create coordinator with real execution
    coord = create_coordinator_v3(use_real_execution=True)
    
    # Execute a task
    await coord.start_task("我想规划一个周末短途旅行")

asyncio.run(main())
```

## Directory Structure

```
blueclawv1.0/
├── blueclaw/
│   ├── core/
│   │   ├── dynamic_thinking_engine.py
│   │   └── execution_blueprint.py
│   ├── skills/
│   │   ├── base_skill.py
│   │   ├── file_skill.py
│   │   ├── shell_skill.py
│   │   ├── code_skill.py
│   │   ├── search_skill.py
│   │   ├── browser_skill.py
│   │   └── skill_registry.py
│   ├── memory/
│   │   ├── working_memory.py
│   │   ├── long_term_memory.py
│   │   └── memory_manager.py
│   └── integration/
│       └── coordinator_v3.py
├── tests/
│   └── test_integration.py
├── launch.py
├── requirements.txt
└── README.md
```

## License

MIT
