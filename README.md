# SelfHeal - Make all code self-healing
## Demo

Demo shows:
1. Slack alert with a link to the debug state (including the full stack trace, variables, and source code)
2. Web viewer to browse and analyze debug states
3. LLM analysis of the root cause and fix suggestions

![Demo](https://raw.githubusercontent.com/OpenExcept/SelfHeal/main/assets/demo.gif)

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
