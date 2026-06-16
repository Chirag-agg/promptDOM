# PromptDOM

A local-first FastAPI application that connects to an already running Chrome browser through the Chrome DevTools Protocol (CDP), receives natural language requests, converts them into structured actions, and executes those actions on the currently active tab.

## Features

- Connect to existing Chrome instance via CDP (no browser extension needed)
- Natural language parsing for browser actions
- Supported actions: hide, show, highlight
- Supported targets: YouTube Shorts, comments, sidebar
- Local-only execution - no cloud services or authentication required

## Project Structure

```
promptdom/
├── promptdom/
│   ├── __init__.py
│   ├── main.py
│   ├── browser.py
│   ├── planner.py
│   ├── runtime.py
│   ├── features.py
│   └── models.py
├── tests/
│   ├── __init__.py
│   └── test_planner.py
├── pyproject.toml
├── .gitignore
├── LICENSE
└── README.md
```

## How to Launch Chrome with Remote Debugging

Before running PromptDOM, you need to launch Chrome with remote debugging enabled:

### Windows
```bash
chrome.exe --remote-debugging-port=9222
```

### macOS
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
```

### Linux
```bash
google-chrome --remote-debugging-port=9222
```

**Note**: Make sure Chrome is not already running, or close all Chrome instances before launching with the debug flag.

## Installation

1. Clone or create the project directory
2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Install Playwright browsers (optional, as we connect to existing Chrome):
   ```bash
   playwright install
   ```

## How to Run

```bash
uvicorn promptdom.main:app --reload
```

The API will be available at http://localhost:8000

## API Endpoints

### POST /execute
Execute a natural language prompt on the active browser tab.

**Request:**
```json
{
  "prompt": "Hide YouTube Shorts"
}
```

**Response:**
```json
{
  "success": true,
  "action": {
    "action": "hide",
    "target": "youtube_shorts"
  },
  "message": "Successfully executed hide on youtube_shorts"
}
```

### Example curl requests

Hide YouTube Shorts:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hide YouTube Shorts"}'
```

Show comments:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show comments"}'
```

Highlight sidebar:
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Highlight sidebar"}'
```

## Supported Actions and Targets

### Actions
- `hide`: Hide elements using `display: none`
- `show`: Show hidden elements
- `highlight`: Add yellow border highlight to elements

### Targets
- `youtube_shorts`: Targets YouTube Shorts shelf (`ytd-reel-shelf-renderer`)
- `comments`: Targets comments section (`#comments`)
- `sidebar`: Targets sidebar (`#secondary`)

## How It Works

1. **Natural Language Parsing**: The planner converts prompts like "Hide YouTube Shorts" into structured JSON `{action: "hide", "target": "youtube_shorts"}`
2. **Feature Registry**: Maps targets to CSS selectors
3. **Runtime Engine**: Generates appropriate JavaScript for each action/target combination
4. **Browser Manager**: Connects to Chrome via CDP and executes JavaScript on the active tab

## Implementation Details

- **promptdom/browser.py**: Handles Chrome DevTools Protocol connection using Playwright
- **promptdom/planner.py**: Rule-based natural language parser (no LLM used)
- **promptdom/features.py**: Registry of target features and their CSS selectors
- **promptdom/runtime.py**: Generates safe, scoped JavaScript for DOM manipulation
- **promptdom/main.py**: FastAPI application with `/execute` endpoint
- **promptdom/models.py**: Pydantic models for request/response validation

## Requirements

- Python 3.12+
- Google Chrome (for CDP connection)
- Internet connection (only for initial dependency installation)

## Security Notes

- Only connects to locally running Chrome instance
- No arbitrary JavaScript execution - all JS is generated internally
- No data leaves your machine
- No authentication or cloud dependencies

## Troubleshooting

If you get connection errors:
1. Ensure Chrome is running with `--remote-debugging-port=9222`
2. Check that no firewall is blocking port 9222
3. Verify you're using the correct Chrome executable path for your OS