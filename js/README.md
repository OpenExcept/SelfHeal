# SelfHeal - Make all code self-healing

## Demo

Demo shows:
1. Slack alert with a link to the debug state (including the full stack trace, variables, and source code)
2. Web viewer to browse and analyze debug states
3. LLM analysis of the root cause and fix suggestions

## Quick Start

1. Install
npm install selfheal-js

2. Configure
export SLACK_BOT_TOKEN="xoxb-your-token"  # Optional

3. Use
const { FunctionDebugger } = require('selfheal-js');

const debugger = new FunctionDebugger({
    dumpDir: "/path/to/debug/states",
    useS3: false,
    slackToken: process.env.SLACK_BOT_TOKEN
});

// Decorate functions
@debugger.debugEnabled()
function myFunction() {
    // ...
}

// Or entire classes
@debugger.debugEnabled()
class MyClass {
    // ...
}
