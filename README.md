# PromptDOM Studio

PromptDOM is a local-first platform designed to instantly restructure and redesign any live website using natural language. 

By capturing a page's DOM, building a structural **Knowledge Graph**, and employing a multi-stage LLM reasoning pipeline, PromptDOM translates high-level aesthetic intent into robust, deterministic frontend CSS/JS code.

## Phase 10 Architecture

PromptDOM operates on a completely decoupled **Multi-Stage Execution Pipeline**:

1. **Intent Interpreter**: Extracts pure design principles from the user's prompt (e.g., "reduce visual noise") without attempting to guess website structure.
2. **Site Context Builder**: Queries the local Knowledge Graph to extract only the concepts relevant to the design intent, preventing the downstream planner from drowning in context.
3. **Impact Analyzer**: Strategically determines how each logical concept should be treated (e.g., `REMOVE Shorts`, `DEEMPHASIZE Sidebar`).
4. **Transformation Planner**: Generates a structural, DOM-agnostic transformation delta consisting of concrete operations.
5. **CSS/JS Engineer**: Receives exact, verified CSS selectors from the Knowledge Graph for the requested concepts and engineers the final CSS/JS code, injecting it live into the browser.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Chrome Browser

### 1. Start the Chrome Debugger
To allow PromptDOM to interact with your live browser, you must start Chrome with remote debugging enabled.
```bash
# Windows
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 2. Start the Backend
```bash
python -m venv .venv
source .venv/Scripts/activate  # Or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# Create a .env file with your LLM provider credentials
# GROQ_API_KEY=...
# OPENAI_API_KEY=...

# Run the server
python run_server.py
```

### 3. Start PromptDOM Studio (Frontend)
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to access PromptDOM Studio.

## Using PromptDOM Studio

1. Open the website you wish to redesign in your Chrome debugger window.
2. In PromptDOM Studio, type your intent in the prompt box (e.g., "Make this site more minimalistic").
3. Click **Execute Redesign**.
4. Use the **Debugger** panel to trace the pipeline's exact reasoning step-by-step (Intent -> Impact Analysis -> Operations).