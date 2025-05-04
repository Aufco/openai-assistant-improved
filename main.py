#!/usr/bin/env python3
"""
Improved OpenAI Assistant with Real-time Command Execution

An interactive assistant that processes user prompts, sends them to the OpenAI API,
executes commands in real-time, and maintains context between API calls.
"""
import os
import sys
import re
import argparse
import time
from typing import List, Dict, Any, Optional
import json
import uuid
import readline  # Enables command history and editing

from context_handler import ConversationContext
from command_executor import execute_commands, filter_commands
from openai_handler import make_openai_request

def get_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Improved OpenAI Assistant with Real-time Command Execution')
    
    # Core settings
    parser.add_argument('--base-prompt', '-b', type=str, default="",
                        help='The base prompt to include in every call')
    parser.add_argument('--prompt', '-p', type=str,
                        help='Initial prompt to start with')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')
    
    # Session management
    parser.add_argument('--session', '-s', type=str,
                        help='Specify a session ID to continue')
    parser.add_argument('--list-sessions', '-l', action='store_true',
                        help='List available sessions')
    parser.add_argument('--session-name', '-n', type=str,
                        help='Name for a new session')
    
    # Execution controls
    parser.add_argument('--max-calls', '-m', type=int, default=20,
                        help='Maximum number of API calls to make')
    parser.add_argument('--auto-loop', '-a', action='store_true',
                        help='Automatically loop using the same prompt')
    parser.add_argument('--loop-delay', '-d', type=int, default=2,
                        help='Delay between loops in seconds (for auto-loop mode)')
    
    # Context controls
    parser.add_argument('--history-limit', type=int, default=10,
                        help='Maximum number of past calls to include in context')
    parser.add_argument('--clear-context', '-c', action='store_true',
                        help='Start with a fresh context')
    
    # Advanced features
    parser.add_argument('--system-info', type=str,
                        help='Override the default system information')
    parser.add_argument('--export-session', '-e', type=str,
                        help='Export a session to a JSON file')
    parser.add_argument('--temperature', '-t', type=float, default=0.7,
                        help='Temperature for OpenAI API (0.0-1.0)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    return parser.parse_args()

def print_banner():
    """Display a banner for the application."""
    banner = """
    ┌───────────────────────────────────────────────┐
    │     OPENAI ASSISTANT WITH COMMAND EXECUTION    │
    │                                               │
    │  Type your prompt, and the assistant will     │
    │  execute commands and provide feedback        │
    │                                               │
    │  Type 'help' for command options              │
    │  Type 'exit' to quit                          │
    └───────────────────────────────────────────────┘
    """
    print(banner)

def print_help():
    """Display help information."""
    help_text = """
    Available Commands:
    ------------------
    help          : Show this help message
    exit, quit    : Exit the program
    clear         : Clear the screen
    sessions      : List available sessions
    switch <id>   : Switch to a different session
    history       : Show history of current session
    context       : Show current context summary
    reset         : Reset the context but stay in the same session
    export <file> : Export current session to a file
    
    Any other input will be treated as a prompt for the AI assistant.
    """
    print(help_text)

def list_sessions(context):
    """List available sessions."""
    sessions = context.get_sessions_list()
    if not sessions:
        print("No sessions found.")
        return
    
    print("\nAvailable Sessions:")
    print("-" * 80)
    print(f"{'ID':<20} {'Name':<30} {'Created':<20} {'Last Updated':<20}")
    print("-" * 80)
    for session in sessions:
        print(f"{session['session_id']:<20} {session['name']:<30} {session['start_time'][:16]:<20} {session['last_updated'][:16]:<20}")
    print("-" * 80)

def get_system_info():
    """Get detailed system information."""
    import platform
    import subprocess
    
    try:
        # Get basic system info
        system_info = f"System: {platform.node()}, {platform.system()} {platform.release()}, {platform.machine()}"
        
        # Add more detailed info for Linux
        if platform.system() == "Linux":
            try:
                with open("/etc/os-release", "r") as f:
                    os_info = dict(line.strip().split('=', 1) for line in f if '=' in line)
                    os_name = os_info.get('PRETTY_NAME', '').strip('"')
                    system_info = f"System: {platform.node()}, {os_name}, {platform.machine()}"
                
                # Get CPU info
                cpu_info = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | uniq", shell=True).decode('utf-8').strip()
                if cpu_info:
                    processor = cpu_info.split(':')[1].strip()
                    system_info += f"\nProcessor: {processor}"
                
                # Get memory info
                mem_info = subprocess.check_output("free -h | grep Mem", shell=True).decode('utf-8').strip()
                if mem_info:
                    system_info += f"\nMemory: {mem_info}"
                
                # Get disk info
                disk_info = subprocess.check_output("df -h / | grep /", shell=True).decode('utf-8').strip()
                if disk_info:
                    system_info += f"\nDisk: {disk_info}"
                
                # Get WSL info if applicable
                try:
                    wsl_info = subprocess.check_output("wsl.exe --status", shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip()
                    if wsl_info:
                        system_info += f"\nWSL: {wsl_info}"
                except:
                    pass
            except:
                pass
        
        system_info += f"\nProject Directory: /home/benau/projects"
        system_info += f"\nPython: {platform.python_version()}"
        
        return system_info
    except Exception as e:
        return f"System: Unknown (Error: {str(e)})"

def extract_commands(response_text):
    """Extract commands from the OpenAI response."""
    command_start_tag = "<command>"
    command_end_tag = "</command>"
    
    pattern = f"{command_start_tag}(.*?){command_end_tag}"
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return ""

def handle_special_command(command, context, session_id, args):
    """Handle special commands like help, exit, etc."""
    command = command.strip().lower()
    
    if command in ('exit', 'quit'):
        print("Goodbye!")
        sys.exit(0)
    
    elif command == 'help':
        print_help()
        return True
    
    elif command == 'clear':
        os.system('cls' if os.name == 'nt' else 'clear')
        return True
    
    elif command == 'sessions':
        list_sessions(context)
        return True
    
    elif command.startswith('switch '):
        new_session_id = command.split(' ', 1)[1].strip()
        sessions = context.get_sessions_list()
        session_ids = [s['session_id'] for s in sessions]
        if new_session_id in session_ids:
            return False, new_session_id
        else:
            print(f"Session {new_session_id} not found.")
            return True
    
    elif command == 'history':
        history = context.get_conversation_history(session_id)
        print("\nSession History:")
        print(history)
        return True
    
    elif command == 'context':
        ctx = context.get_openai_context(session_id, args.history_limit)
        print("\nCurrent Context Summary:")
        print(f"Session: {ctx['session']['name']} ({ctx['session']['session_id']})")
        print(f"Started: {ctx['session']['start_time']}")
        print(f"Last Updated: {ctx['session']['last_updated']}")
        print(f"Messages in Context: {len(ctx['messages'])}")
        return True
    
    elif command == 'reset':
        return False, 'reset'
    
    elif command.startswith('export '):
        filename = command.split(' ', 1)[1].strip()
        ctx = context.get_openai_context(session_id)
        with open(filename, 'w') as f:
            json.dump(ctx, f, indent=2)
        print(f"Exported session to {filename}")
        return True
    
    return False

def run_assistant_loop(args, context, session_id):
    """
    Run the assistant loop with improved interactivity.
    
    Args:
        args: Command-line arguments
        context: ConversationContext instance
        session_id: Current session ID
    """
    call_number = 1
    completed_calls = 0
    prompt = args.prompt
    
    while completed_calls < args.max_calls:
        if not prompt:
            if args.interactive:
                try:
                    prompt = input("\n\033[1;36m> \033[0m").strip()
                    
                    # Handle special commands
                    if prompt:
                        result = handle_special_command(prompt, context, session_id, args)
                        if result is True:
                            prompt = None
                            continue
                        elif isinstance(result, tuple):
                            if result[1] == 'reset':
                                # Reset context but stay in same session
                                print("Resetting context for this session...")
                                # Clear all messages but keep session
                                session_id = context.create_session(
                                    get_system_info(),
                                    args.base_prompt,
                                    args.session_name or f"Session {session_id}"
                                )
                                call_number = 1
                                prompt = None
                                continue
                            else:
                                # Switch to a different session
                                session_id = result[1]
                                print(f"Switched to session: {session_id}")
                                call_number = len(context.get_session_messages(session_id)) + 1
                                prompt = None
                                continue
                except KeyboardInterrupt:
                    print("\nInterrupted by user.")
                    break
                except EOFError:
                    print("\nEnd of input. Exiting.")
                    break
            else:
                print("No prompt provided. Exiting.")
                break
        
        # Print call information
        print(f"\n\033[1;32m=== CALL #{call_number} ({completed_calls + 1}/{args.max_calls}) ===\033[0m")
        if args.verbose:
            print(f"\033[0;37mPrompt: {prompt}\033[0m")
        
        # Add user message to context
        context.add_message(session_id, "user", prompt, call_number)
        
        # Get context for API request
        api_context = context.get_openai_context(session_id, args.history_limit)
        
        # Make API request
        response_text = make_openai_request(
            api_context["messages"],
            temperature=args.temperature
        )
        
        # Extract commands
        commands = extract_commands(response_text)
        
        # Add assistant message to context
        message_id = context.add_message(session_id, "assistant", response_text, call_number)
        
        # Print the response (excluding command blocks which we'll execute separately)
        response_without_commands = re.sub(r'<command>.*?</command>', 
                                         '<command>...</command>', 
                                         response_text, 
                                         flags=re.DOTALL)
        print("\n\033[1;34mAssistant:\033[0m")
        print(response_without_commands)
        
        # Execute commands if any
        if commands:
            print("\n\033[1;33mExecuting Commands:\033[0m")
            
            # Check for potentially dangerous commands
            filtered_commands, skipped_lines = filter_commands(commands)
            
            if skipped_lines:
                print("\n\033[1;31mWARNING: Skipped potentially unsafe commands:\033[0m")
                for line_num, cmd in skipped_lines:
                    print(f"  Line {line_num}: {cmd}")
                
                if args.interactive:
                    proceed = input("\nSome commands were flagged as potentially unsafe. Proceed? (y/n): ")
                    if proceed.lower() != 'y':
                        print("Execution aborted by user.")
                        output = "Execution aborted by user due to potentially unsafe commands."
                        context.add_command(session_id, message_id, commands, output, 1, 0.0)
                        break
            
            # Execute the commands
            start_time = time.time()
            output = execute_commands(filtered_commands)
            execution_time = time.time() - start_time
            
            # Determine exit code (approximate from output)
            exit_code = 0 if "ERROR:" not in output else 1
            
            # Add command to context
            context.add_command(session_id, message_id, commands, output, exit_code, execution_time)
        
        # Increment call number and completed calls counter
        call_number += 1
        completed_calls += 1
        
        # Check if we've reached the maximum number of calls
        if completed_calls >= args.max_calls:
            print(f"\n\033[1;32mReached maximum number of calls ({args.max_calls}). Exiting.\033[0m")
            break
        
        # Determine next prompt
        if args.auto_loop:
            # In auto-loop mode, keep using the same prompt
            time.sleep(args.loop_delay)
            print(f"\nAuto-looping with delay of {args.loop_delay} seconds...")
            # prompt remains the same
        elif args.interactive:
            # Interactive mode - we'll get the next prompt at the top of the loop
            prompt = None
        else:
            # If not interactive or auto-loop, we're done after one call
            break
    
    print("\n\033[1;32mSession complete.\033[0m")
    print(f"Session ID: {session_id}")
    return session_id

def main():
    """Main entry point for the application."""
    args = get_args()
    
    # Initialize context handler
    context = ConversationContext()
    
    # Handle listing sessions
    if args.list_sessions:
        list_sessions(context)
        sys.exit(0)
    
    # Handle exporting a session
    if args.export_session:
        sessions = context.get_sessions_list()
        session_ids = [s['session_id'] for s in sessions]
        
        if args.export_session in session_ids:
            ctx = context.get_openai_context(args.export_session)
            export_file = f"session_{args.export_session}.json"
            with open(export_file, 'w') as f:
                json.dump(ctx, f, indent=2)
            print(f"Exported session to {export_file}")
        else:
            print(f"Session {args.export_session} not found.")
        
        sys.exit(0)
    
    # Get or create session ID
    session_id = None
    if args.session:
        sessions = context.get_sessions_list()
        session_ids = [s['session_id'] for s in sessions]
        
        if args.session in session_ids:
            session_id = args.session
            print(f"Continuing session: {session_id}")
        else:
            print(f"Session {args.session} not found. Creating a new session.")
    
    if not session_id:
        # Create a new session
        system_info = args.system_info if args.system_info else get_system_info()
        session_id = context.create_session(
            system_info,
            args.base_prompt or "I am an AI assistant that helps with executing commands and providing information.",
            args.session_name
        )
        print(f"Created new session: {session_id}")
    
    # Display banner in interactive mode
    if args.interactive:
        print_banner()
    
    # Run the assistant loop
    session_id = run_assistant_loop(args, context, session_id)
    
    print(f"\nSession {session_id} completed.")
    
if __name__ == "__main__":
    main()
