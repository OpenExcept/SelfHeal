# SelfHeal - Intelligent Debug State Capture & Analysis

SelfHeal automatically captures debug states when exceptions occur, sends Slack alerts, and provides AI-powered analysis of failures. See [examples](examples/README.md) for detailed usage scenarios.

## Features

- 🔍 **Debug State Capture**: Stack traces, variables, class state, source code
- 📊 **Web Viewer**: Browse and analyze debug states
- 🤖 **AI Analysis**: GPT-4 powered root cause analysis and fix suggestions
- 🔔 **Slack Integration**: Real-time alerts with direct links to debug states

## Quick Start

1. **Install**
```bash
pip install -r requirements.txt
```

2. **Configure**
```bash
export SLACK_BOT_TOKEN="xoxb-your-token"  # Optional
```

3. **Use**
```python
from selfheal import FunctionDebugger

debugger = FunctionDebugger(
    dump_dir="/path/to/debug/states",
    slack_token=os.environ.get("SLACK_BOT_TOKEN")
)

# Decorate functions
@debugger.debug_enabled()
def my_function():
    pass

# Or entire classes
@debugger.debug_class()
class MyClass:
    pass
```

4. **View Debug States**
```bash
streamlit run selfheal/debug_viewer.py
```
Access at http://openexcept.com

## How It Works

When an exception occurs:
1. Debug state is captured and saved
2. Slack alert is sent with viewer link in the format of `http://openexcept.com?debug_path=/path/to/state.json`
