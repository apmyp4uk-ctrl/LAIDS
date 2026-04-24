#!/usr/bin/env python3
"""AI Factory - Startup script."""
import asyncio
import argparse
import sys
import uvicorn
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.main import MainOrchestrator
from webui import app


async def run_simple_task():
    """Run a simple test task."""
    print("=" * 50)
    print("AI Factory - Simple Task Runner")
    print("=" * 50)
    
    orchestrator = MainOrchestrator()
    await orchestrator.start()
    
    # Test hello world
    print("\n--- Test: Hello World ---")
    result = await orchestrator.execute_task(
        "Create a Python hello world program that prints 'Hello, World!'",
        "Hello World",
        "coder"
    )
    print(f"Result: {result}")
    
    await orchestrator.stop()


async def run_workflow():
    """Run complete workflow."""
    print("=" * 50)
    print("AI Factory - Complete Workflow")
    print("=" * 50)
    
    orchestrator = MainOrchestrator()
    await orchestrator.start()
    
    print("\n--- Workflow: Create and Test Hello World ---")
    result = await orchestrator.run_workflow(
        "Create a hello world program in Python that prints 'Hello, World!'"
    )
    print(f"\nWorkflow Result: {result}")
    
    usage = orchestrator.token_counter.get_usage()
    print(f"Token Usage: {usage}")
    
    await orchestrator.stop()


def run_web():
    """Run web interface."""
    print("=" * 50)
    print("AI Factory - Web Interface")
    print("Starting on http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Factory")
    parser.add_argument('--mode', choices=['task', 'workflow', 'web'], default='task',
                    help='Run mode')
    parser.add_argument('--description', default='',
                    help='Task description')
    parser.add_argument('--port', type=int, default=8000,
                    help='Web interface port')
    args = parser.parse_args()
    
    if args.mode == 'web':
        run_web()
    elif args.mode == 'workflow':
        await run_workflow()
    else:
        if args.description:
            print("=" * 50)
            print("AI Factory - Task Runner")
            print("=" * 50)
            
            orchestrator = MainOrchestrator()
            await orchestrator.start()
            
            result = await orchestrator.execute_task(
                args.description,
                "User Task",
                "coder"
            )
            print(f"\nResult: {result}")
            
            await orchestrator.stop()
        else:
            await run_simple_task()


if __name__ == "__main__":
    asyncio.run(main())