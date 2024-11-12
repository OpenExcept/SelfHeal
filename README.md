# SelfHeal - Make all code self-healing

SelfHeal helps your code achieve self healing, by automatically captures debug states when exceptions occur, sends Slack alerts, and provide LLM analysis of how to fix the root cause. See [examples](examples/README.md) for detailed usage scenarios.

## Demo

The demo below demos 3 key features:
1. Slack alert with a link to the debug state
2. Web viewer to browse and analyze debug states
3. LLM analysis of the root cause and fix suggestions

![Demo](https://github.com/OpenExcept/SelfHeal/blob/main/assets/demo.gif)

## Quick Start

1. **Install**
```bash
pip install selfheal
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
Access example at http://openexcept.com

## How It Works

When an exception occurs:
1. Debug state is captured and saved
2. Slack alert is sent with viewer link in the format of `http://openexcept.com?debug_path=/path/to/state.json`
