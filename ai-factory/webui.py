"""Web interface for AI Factory."""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
from pathlib import Path


app = FastAPI(title="AI Factory")
templates = Jinja2Templates(directory="templates")


# HTML Template for the web interface
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Factory</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #16213e;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #0f3460;
        }
        .header h1 { color: #e94560; font-size: 1.5rem; }
        .status { display: flex; gap: 1rem; align-items: center; }
        .status-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #00ff00;
        }
        .main { flex: 1; display: flex; overflow: hidden; }
        .sidebar {
            width: 250px;
            background: #16213e;
            padding: 1rem;
            border-right: 1px solid #0f3460;
        }
        .sidebar h3 { margin-bottom: 1rem; color: #888; font-size: 0.8rem; text-transform: uppercase; }
        .nav-item {
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            cursor: pointer;
            transition: 0.2s;
        }
        .nav-item:hover, .nav-item.active {
            background: #0f3460;
        }
        .content { flex: 1; display: flex; flex-direction: column; }
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 1rem;
            overflow: hidden;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }
        .message {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 12px;
            max-width: 80%;
        }
        .message.user {
            background: #0f3460;
            margin-left: auto;
        }
        .message.ai {
            background: #16213e;
        }
        .input-area {
            display: flex;
            gap: 0.5rem;
            padding: 1rem;
            background: #16213e;
            border-top: 1px solid #0f3460;
        }
        .input-area input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: 8px;
            background: #1a1a2e;
            color: #eee;
            font-size: 1rem;
        }
        .input-area button {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            background: #e94560;
            color: white;
            cursor: pointer;
            font-weight: 600;
        }
        .input-area button:hover { background: #d63d56; }
        
        /* Code Editor Tab */
        .code-container {
            display: none;
            flex: 1;
            flex-direction: column;
        }
        .code-container.active { display: flex; }
        .editor-toolbar {
            display: flex;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: #16213e;
        }
        .editor-toolbar button {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            background: #0f3460;
            color: #eee;
            cursor: pointer;
        }
        .editor {
            flex: 1;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            background: #1a1a2e;
            color: #00ff00;
            border: none;
            resize: none;
            font-size: 14px;
            line-height: 1.5;
        }
        
        /* Terminal Tab */
        .terminal-container {
            display: none;
            flex: 1;
            background: #0a0a0a;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            color: #00ff00;
            overflow-y: auto;
        }
        .terminal-container.active { display: block; }
        
        /* Metrics */
        .metrics {
            display: flex;
            gap: 1rem;
            padding: 1rem;
        }
        .metric-card {
            background: #16213e;
            padding: 1rem;
            border-radius: 8px;
            min-width: 120px;
        }
        .metric-value { font-size: 1.5rem; font-weight: 600; color: #e94560; }
        .metric-label { font-size: 0.8rem; color: #888; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Factory</h1>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Ready</span>
        </div>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <h3>Navigation</h3>
            <div class="nav-item active" onclick="showTab('chat')">💬 Chat</div>
            <div class="nav-item" onclick="showTab('code')">💻 Code Editor</div>
            <div class="nav-item" onclick="showTab('terminal')">⌨️ Terminal</div>
            <div class="nav-item" onclick="showTab('metrics')">📊 Metrics</div>
            
            <h3 style="margin-top: 2rem;">Agents</h3>
            <div class="nav-item">🧠 Planner</div>
            <div class="nav-item">👨‍💻 Coder</div>
            <div class="nav-item">🧪 Tester</div>
            <div class="nav-item">🔧 Debug</div>
            <div class="nav-item">🔍 Researcher</div>
        </div>
        
        <div class="content">
            <!-- Chat Tab -->
            <div class="chat-container" id="chatTab">
                <div class="messages" id="messages"></div>
                <div class="input-area">
                    <input type="text" id="chatInput" placeholder="Ask AI Factory..." onkeypress="handleKey(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <!-- Code Editor Tab -->
            <div class="code-container" id="codeTab">
                <div class="editor-toolbar">
                    <button onclick="runCode()">▶ Run</button>
                    <button onclick="saveCode()">💾 Save</button>
                    <button onclick="clearCode()">🗑️ Clear</button>
                </div>
                <textarea class="editor" id="codeEditor" placeholder="# Write your code here..."></textarea>
            </div>
            
            <!-- Terminal Tab -->
            <div class="terminal-container" id="terminalTab">
                <div>AI Factory Terminal v0.1.0</div>
                <div>Type 'help' for commands</div>
                <br>
                <div id="terminalOutput"></div>
            </div>
            
            <!-- Metrics Tab -->
            <div class="chat-container" id="metricsTab" style="display:none">
                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-value" id="tasksCompleted">0</div>
                        <div class="metric-label">Tasks Completed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="tokensUsed">0</div>
                        <div class="metric-label">Tokens Used</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="uptime">0s</div>
                        <div class="metric-label">Uptime</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let startTime = Date.now();
        
        function showTab(tab) {
            // Update nav
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.target.closest('.nav-item')?.classList.add('active');
            
            // Show content
            document.getElementById('chatTab').style.display = tab === 'chat' ? 'flex' : 'none';
            document.getElementById('codeTab').classList.toggle('active', tab === 'code');
            document.getElementById('terminalTab').classList.toggle('active', tab === 'terminal');
            document.getElementById('metricsTab').style.display = tab === 'metrics' ? 'flex' : 'none';
        }
        
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const messages = document.getElementById('messages');
            const text = input.value.trim();
            if (!text) return;
            
            // Add user message
            messages.innerHTML += `<div class="message user">${escapeHtml(text)}</div>`;
            input.value = '';
            
            // Show thinking
            messages.innerHTML += `<div class="message ai">🤔 Thinking...</div>`;
            messages.scrollTop = messages.scrollHeight;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await response.json();
                
                // Replace thinking with response
                messages.lastElementChild.remove();
                messages.innerHTML += `<div class="message ai">${escapeHtml(data.response || data.error)}</div>`;
            } catch (e) {
                messages.lastElementChild.remove();
                messages.innerHTML += `<div class="message ai">❌ Error: ${e}</div>`;
            }
            
            messages.scrollTop = messages.scrollHeight;
        }
        
        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }
        
        function escapeHtml(text) {
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        async function runCode() {
            const code = document.getElementById('codeEditor').value;
            await fetch('/api/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code})
            });
        }
        
        function saveCode() {
            // Save to file
            localStorage.setItem('code', document.getElementById('codeEditor').value);
            alert('Code saved!');
        }
        
        function clearCode() {
            document.getElementById('codeEditor').value = '';
        }
        
        // Update uptime
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const mins = Math.floor((elapsed % 3600) / 60);
            const secs = elapsed % 60;
            document.getElementById('uptime').textContent = 
                hours > 0 ? `${hours}h ${mins}m` : `${mins}m ${secs}s`;
        }, 1000);
    </script>
</body>
</html>
"""


# Create templates directory and index.html
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page."""
    return HTML_CONTENT


@app.get("/api/status")
async def get_status():
    """Get system status."""
    return {"status": "running", "version": "0.1.0"}


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    return {
        "tasks_completed": 0,
        "tokens_used": 0,
        "uptime_seconds": 0
    }


@app.post("/api/chat")
async def chat(request: Request):
    """Handle chat messages."""
    data = await request.json()
    message = data.get("message", "")
    
    return {"response": f"Echo: {message}"}


@app.post("/api/run")
async def run_code(request: Request):
    """Run code."""
    data = await request.json()
    code = data.get("code", "")
    
    return {"status": "submitted"}


def start_web_interface(port: int = 8000):
    """Start the web interface."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    return server


if __name__ == "__main__":
    print("Starting AI Factory Web Interface on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)