"""
Command execution handler for the OpenAI Assistant Project with real-time output.
"""
import os
import re
import subprocess
import tempfile
import time
import shlex
import sys
from threading import Thread
from queue import Queue, Empty

def read_output(pipe, queue):
    """Read output from a pipe and put it in a queue."""
    for line in iter(pipe.readline, b''):
        queue.put(line.decode('utf-8'))
    pipe.close()

def execute_command_realtime(command, prefix=""):
    """
    Execute a single command with real-time output display.
    
    Args:
        command (str): Command to execute
        prefix (str, optional): Prefix to display before each line of output
        
    Returns:
        tuple: (exit_code, full_output)
    """
    # Print the command being executed
    print(f"\n{prefix}$ {command}")
    sys.stdout.flush()
    
    # Start the command process
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=False
    )
    
    # Set up queues for stdout and stderr
    stdout_queue = Queue()
    stderr_queue = Queue()
    
    # Set up threads to read stdout and stderr
    stdout_thread = Thread(target=read_output, args=(process.stdout, stdout_queue))
    stderr_thread = Thread(target=read_output, args=(process.stderr, stderr_queue))
    
    # Start threads
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    # Collect full output for return
    full_output = []
    
    # Read and display output in real-time
    while True:
        # Check if process has finished
        if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
            break
        
        # Read from stdout queue
        try:
            stdout_line = stdout_queue.get_nowait()
            print(f"{prefix}> {stdout_line}", end='')
            sys.stdout.flush()
            full_output.append(stdout_line)
        except Empty:
            pass
        
        # Read from stderr queue
        try:
            stderr_line = stderr_queue.get_nowait()
            print(f"{prefix}! {stderr_line}", end='')
            sys.stdout.flush()
            full_output.append(f"ERROR: {stderr_line}")
        except Empty:
            pass
        
        time.sleep(0.1)
    
    # Join threads to ensure they are complete
    stdout_thread.join()
    stderr_thread.join()
    
    return process.returncode, ''.join(full_output)

def execute_commands(commands, timeout=300):
    """
    Execute a series of shell commands with real-time output.
    
    Args:
        commands (str): Commands to execute, separated by newlines
        timeout (int, optional): Command execution timeout in seconds
        
    Returns:
        str: Command output or error message
    """
    if not commands.strip():
        return "No commands to execute."
    
    # Split commands into individual lines
    command_lines = [cmd for cmd in commands.split('\n') if cmd.strip() and not cmd.strip().startswith('#')]
    
    print("\n=== Starting Command Execution ===")
    output_parts = []
    start_time = time.time()
    
    for i, cmd in enumerate(command_lines):
        # Check for timeout
        if time.time() - start_time > timeout:
            output_parts.append(f"\nERROR: Command execution timed out after {timeout} seconds.")
            break
        
        command_prefix = f"[{i+1}/{len(command_lines)}]"
        exit_code, cmd_output = execute_command_realtime(cmd, prefix=command_prefix)
        
        output_parts.append(f"\n# Command {i+1}: {cmd}")
        output_parts.append(cmd_output)
        
        if exit_code != 0:
            output_parts.append(f"\nERROR: Command failed with exit code {exit_code}")
            break
    
    execution_time = time.time() - start_time
    output_parts.append(f"\n=== Execution completed in {execution_time:.2f} seconds ===")
    
    return '\n'.join(output_parts)

def is_safe_command(command):
    """
    Check if a command is considered safe to execute.
    
    Args:
        command (str): The command to check
        
    Returns:
        bool: True if command is safe, False otherwise
    """
    # List of potentially dangerous command patterns
    dangerous_patterns = [
        r'rm\s+-rf\s+[/~]',  # Remove root or home
        r'mkfs',             # Format filesystems
        r'dd\s+if=/dev/zero', # Disk destroyer
        r':(){:|:&};:',      # Fork bomb
        r'chmod\s+-R\s+777\s+[/~]', # Recursive permission change
        r'wget.+\s+\|\s+bash', # Download and execute
        r'curl.+\s+\|\s+bash', # Download and execute
    ]
    
    # Check each dangerous pattern
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    
    return True

def filter_commands(commands):
    """
    Filter out potentially dangerous commands.
    
    Args:
        commands (str): Commands to check, separated by newlines
        
    Returns:
        tuple: (filtered_commands, skipped_lines)
    """
    lines = commands.split('\n')
    filtered_lines = []
    skipped_lines = []
    
    for i, line in enumerate(lines):
        # Skip empty lines or comments
        if not line.strip() or line.strip().startswith('#'):
            filtered_lines.append(line)
            continue
        
        if is_safe_command(line):
            filtered_lines.append(line)
        else:
            # Replace dangerous command with warning comment
            filtered_lines.append(f"# SKIPPED POTENTIALLY UNSAFE COMMAND (line {i+1}): {line}")
            skipped_lines.append((i+1, line))
    
    return '\n'.join(filtered_lines), skipped_lines
