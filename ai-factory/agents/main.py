"""AI Factory - Main agent orchestration system with tools."""
import asyncio
import os
import sys
import signal
import subprocess
import shlex
import re
from pathlib import Path
from typing import Optional, Any, List, Dict
from datetime import datetime
import logging
import aiofiles
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import config
from utils.logger import AIFactoryLogger, TokenCounter
from utils.adapters import AdapterManager
from utils.queue import TaskQueue, Task, TaskStatus


# ============================================================
# AGENT TOOLS
# ============================================================

class AgentTools:
    """Tools available to all agents."""
    
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace)
        self.logger = logging.getLogger('ai-factory.tools')
    
    # 📁 FILE OPERATIONS
    async def read_file(self, path: str) -> str:
        """Read file content."""
        try:
            async with aiofiles.open(path, 'r') as f:
                return await f.read()
        except Exception as e:
            return f"Error: {e}"
    
    async def write_file(self, path: str, content: str) -> Dict:
        """Write content to file."""
        try:
            async with aiofiles.open(path, 'w') as f:
                await f.write(content)
            return {'status': 'success', 'path': path}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def edit_file(self, path: str, old: str, new: str) -> Dict:
        """Edit file content (replace old with new)."""
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
            content = content.replace(old, new)
            async with aiofiles.open(path, 'w') as f:
                await f.write(content)
            return {'status': 'success', 'path': path}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def list_files(self, pattern: str = "*") -> List[str]:
        """List files matching pattern."""
        try:
            files = list(self.workspace.glob(pattern))
            return [str(f) for f in files]
        except Exception as e:
            return [f"Error: {e}"]
    
    # 💻 TERMINAL
    async def run_command(self, cmd: str, timeout: int = 30) -> Dict:
        """Run shell command."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=timeout,
                cwd=str(self.workspace)
            )
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'error': 'Timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def run_background(self, cmd: str) -> Dict:
        """Run command in background."""
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.workspace)
            )
            return {
                'status': 'success',
                'pid': proc.pid,
                'message': f'Started process {proc.pid}'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    # 🔍 SEARCH
    async def grep(self, pattern: str, files: str = "*.py") -> List[Dict]:
        """Search pattern in files."""
        results = []
        try:
            for path in self.workspace.glob(files):
                try:
                    async with aiofiles.open(path, 'r') as f:
                        content = await f.read()
                    for i, line in enumerate(content.split('\n'), 1):
                        if re.search(pattern, line):
                            results.append({
                                'file': str(path),
                                'line': i,
                                'content': line.strip()
                            })
                except:
                    pass
        except Exception as e:
            return [{'error': str(e)}]
        return results
    
    async def find_files(self, name: str) -> List[str]:
        """Find files by name pattern."""
        try:
            files = list(self.workspace.rglob(f"*{name}*"))
            return [str(f) for f in files if f.is_file()]
        except Exception as e:
            return [f"Error: {e}"]
    
    # 🏃 CODE EXECUTION
    async def run_python(self, code: str = None, file: str = None) -> Dict:
        """Run Python code/file."""
        try:
            if file:
                result = subprocess.run(
                    ['python', str(file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(self.workspace)
                )
            else:
                result = subprocess.run(
                    ['python', '-c', code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'error': 'Timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def run_node(self, file: str = None) -> Dict:
        """Run Node.js file."""
        try:
            result = subprocess.run(
                ['node', str(file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace)
            )
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    # 🔧 LINTERS
    async def lint_python(self, file: str) -> Dict:
        """Lint Python file with flake8."""
        try:
            result = subprocess.run(
                ['flake8', file, '--format=%(row)d:%(col)d: %(code)s %(text)s'],
                capture_output=True,
                text=True,
                cwd=str(self.workspace)
            )
            return {
                'status': 'success',
                'issues': result.stdout.strip().split('\n') if result.stdout else []
            }
        except FileNotFoundError:
            # Try pylint
            try:
                result = subprocess.run(
                    ['pylint', file, '--output-format=text'],
                    capture_output=True,
                    text=True,
                    cwd=str(self.workspace)
                )
                return {
                    'status': 'success', 
                    'issues': result.stdout.strip().split('\n')[:10]
                }
            except:
                return {'status': 'warning', 'message': 'No linter available'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def lint_js(self, file: str) -> Dict:
        """Lint JS file with eslint."""
        try:
            result = subprocess.run(
                ['npx', 'eslint', file],
                capture_output=True,
                text=True,
                cwd=str(self.workspace)
            )
            return {
                'status': 'success',
                'issues': result.stdout.strip().split('\n') if result.stdout else []
            }
        except Exception as e:
            return {'status': 'warning', 'message': f'No eslint: {e}'}


class Agent:
    """Base agent for AI Factory."""
    
    def __init__(self, name: str, role: str, config: dict, logger: AIFactoryLogger, tools: AgentTools = None):
        self.name = name
        self.role = role
        self.config = config
        self.logger = logger
        self.tools = tools or AgentTools()
        self.is_running = False
        self.current_task: Optional[Task] = None
    
    async def start(self):
        """Start agent."""
        self.is_running = True
        self.logger.info(f"Agent {self.name} started with role: {self.role}")
    
    async def stop(self):
        """Stop agent."""
        self.is_running = False
        self.logger.info(f"Agent {self.name} stopped")
    
    async def execute(self, task: Task) -> Any:
        """Execute task."""
        self.current_task = task
        self.logger.info(f"Agent {self.name} executing task: {task.name}")
        return None


class PlannerAgent(Agent):
    """Planning agent."""
    
    def __init__(self, config: dict, logger: AIFactoryLogger, adapters: AdapterManager):
        super().__init__("Planner", "planning", config, logger)
        self.adapters = adapters
    
    async def execute(self, task: Task) -> Any:
        """Create execution plan."""
        prompt = f"""Create a detailed execution plan for: {task.description}
        
Respond in JSON format:
{{
    "steps": ["step 1", "step 2", ...],
    "estimated_time": "X minutes",
    "required_agents": ["agent1", "agent2"],
    "resources_needed": ["resource1", ...]
}}"""
        
        adapter = self.adapters.get(self.adapters.select_adapter('reasoning'))
        if adapter:
            try:
                result = await adapter.generate(prompt)
                return {'plan': result, 'status': 'success'}
            except Exception as e:
                self.logger.warning(f"Adapter error: {e}, using fallback")
        
        # Fallback when no LLM available
        return {'plan': {'steps': ['Analyze task'], 'estimated_time': '1 minute'}, 'status': 'fallback'}


class CoderAgent(Agent):
    """Coding agent."""
    
    def __init__(self, config: dict, logger: AIFactoryLogger, adapters: AdapterManager):
        super().__init__("Coder", "coding", config, logger)
        self.adapters = adapters
    
    async def execute(self, task: Task) -> Any:
        """Generate code."""
        prompt = f"""Write code for: {task.description}

Requirements:
- Clean, efficient code
- Include proper error handling
- Add docstrings where needed
- Return only the code, no explanations"""
        
        adapter = self.adapters.get(self.adapters.select_adapter('coding'))
        if adapter:
            try:
                result = await adapter.generate(prompt)
                return {'code': result, 'status': 'success'}
            except Exception as e:
                self.logger.warning(f"Adapter error: {e}, using fallback")
        
        # Fallback
        hello_code = '''#!/usr/bin/env python3
"""Hello World program."""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        return {'code': hello_code, 'status': 'fallback'}


class TesterAgent(Agent):
    """Testing agent."""
    
    def __init__(self, config: dict, logger: AIFactoryLogger, adapters: AdapterManager):
        super().__init__("Tester", "testing", config, logger)
        self.adapters = adapters
    
    async def execute(self, task: Task) -> Any:
        """Test code."""
        prompt = f"""Create test cases for: {task.description}

Return in Python pytest format:
- Test class and methods
- Proper assertions
- Edge case tests"""
        
        adapter = self.adapters.get(self.adapters.select_adapter('fast'))
        if adapter:
            try:
                result = await adapter.generate(prompt)
                return {'tests': result, 'status': 'success'}
            except Exception as e:
                self.logger.warning(f"Adapter error: {e}, using fallback")
        
        # Fallback
        return {'tests': '# Test placeholder', 'status': 'fallback'}


class DebugAgent(Agent):
    """Debugging agent."""
    
    def __init__(self, config: dict, logger: AIFactoryLogger, adapters: AdapterManager):
        super().__init__("Debug", "debugging", config, logger)
        self.adapters = adapters
    
    async def execute(self, task: Task) -> Any:
        """Debug issues."""
        prompt = f"""Analyze and debug: {task.description}

Provide:
- Root cause analysis
- Suggested fix
- Prevention strategy"""
        
        adapter = self.adapters.get(self.adapters.select_adapter('reasoning'))
        if adapter:
            try:
                result = await adapter.generate(prompt)
                return {'debug': result, 'status': 'success'}
            except Exception as e:
                self.logger.warning(f"Adapter error: {e}, using fallback")
        
        # Fallback
        return {'debug': 'Use logging to debug the issue', 'status': 'fallback'}


class ResearcherAgent(Agent):
    """Research agent."""
    
    def __init__(self, config: dict, logger: AIFactoryLogger, adapters: AdapterManager):
        super().__init__("Researcher", "research", config, logger)
        self.adapters = adapters
    
    async def execute(self, task: Task) -> Any:
        """Research topic."""
        prompt = f"""Research: {task.description}

Provide:
- Summary
- Key findings
- Relevant resources"""
        
        adapter = self.adapters.get(self.adapters.select_adapter('general'))
        if adapter:
            try:
                result = await adapter.generate(prompt)
                return {'research': result, 'status': 'success'}
            except Exception as e:
                self.logger.warning(f"Adapter error: {e}, using fallback")
        
        # Fallback
        return {'research': 'Need more information to research', 'status': 'fallback'}


class MainOrchestrator:
    """Main orchestrator agent."""
    
    def __init__(self):
        # Load configuration
        self.config_data = config.config
        self.logger = AIFactoryLogger('ai-factory', self.config_data)
        self.token_counter = TokenCounter(self.config_data)
        
        # Initialize components
        self.adapters = AdapterManager(self.config_data)
        self.task_queue = TaskQueue(self.config_data.get('queue', {}).get('max_size', 100))
        
        # Initialize agents
        agent_config = self.config_data.get('agents', {})
        self.agents = {
            'planner': PlannerAgent(self.config_data, self.logger, self.adapters),
            'coder': CoderAgent(self.config_data, self.logger, self.adapters),
            'tester': TesterAgent(self.config_data, self.logger, self.adapters),
            'debug': DebugAgent(self.config_data, self.logger, self.adapters),
            'researcher': ResearcherAgent(self.config_data, self.logger, self.adapters),
        }
        
        # State
        self.is_running = False
        self._tasks = []
    
    async def start(self):
        """Start the orchestrator."""
        self.is_running = True
        self.logger.info("AI Factory Orchestrator starting...")
        self.logger.info(f"Available adapters: {self.adapters.get_enabled()}")
        
        # Start all agents
        for agent in self.agents.values():
            await agent.start()
        
        self.logger.info("AI Factory Orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator."""
        self.is_running = False
        self.logger.info("AI Factory Orchestrator stopping...")
        
        for agent in self.agents.values():
            await agent.stop()
        
        self.logger.info("AI Factory Orchestrator stopped")
    
    async def execute_task(self, description: str, name: str = "", 
                      agent_type: str = "planner") -> dict:
        """Execute a task end-to-end."""
        task = Task(
            name=name or description[:50],
            description=description,
            payload={'agent_type': agent_type}
        )
        
        self.logger.info(f"Executing task: {task.name}")
        
        # Get appropriate agent
        agent = self.agents.get(agent_type)
        if not agent:
            return {'status': 'error', 'error': f'Unknown agent: {agent_type}'}
        
        # Execute
        try:
            result = await agent.execute(task)
            await self.task_queue.complete(task.id, result)
            return {'status': 'success', 'result': result}
        except Exception as e:
            await self.task_queue.fail(task.id, str(e))
            self.logger.error(f"Task failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def run_workflow(self, task_description: str) -> dict:
        """Run complete workflow: plan -> code -> test -> debug."""
        results = {}
        
        # Plan
        self.logger.info("Workflow: Planning phase")
        plan_result = await self.execute_task(
            task_description, 
            "Planning", 
            "planner"
        )
        results['plan'] = plan_result
        
        # Code
        self.logger.info("Workflow: Coding phase")
        code_result = await self.execute_task(
            task_description,
            "Coding",
            "coder"
        )
        results['code'] = code_result
        
        # Test
        self.logger.info("Workflow: Testing phase")
        test_result = await self.execute_task(
            task_description,
            "Testing",
            "tester"
        )
        results['tests'] = test_result
        
        return results


async def main():
    """Main entry point."""
    print("=" * 50)
    print("AI Factory - Software Development System")
    print("=" * 50)
    
    orchestrator = MainOrchestrator()
    
    try:
        await orchestrator.start()
        
        # Test with hello world example
        print("\n--- Testing Hello World Task ---")
        result = await orchestrator.execute_task(
            "Create a hello world program in Python that prints 'Hello, World!'",
            "Hello World",
            "coder"
        )
        print(f"\nResult: {result}")
        
        # Show token usage
        usage = orchestrator.token_counter.get_usage()
        print(f"\nToken Usage: {usage}")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await orchestrator.stop()
    
    print("\nAI Factory stopped")


if __name__ == "__main__":
    asyncio.run(main())