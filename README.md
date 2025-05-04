# Enhanced OpenAI Assistant with Command Execution

An interactive assistant that processes user prompts, sends them to the OpenAI API, executes commands in real-time, and maintains context between API calls. This project is similar to a simplified version of AutoGPT.

## Features

- **Interactive Command Execution**: See commands being executed in real-time
- **Improved Context Management**: SQLite-based context storage for better persistence
- **Session Management**: Create, switch between, and manage multiple conversation sessions
- **Enhanced User Interface**: Colorized output and clear visual separation
- **Real-time Command Output**: Watch commands execute as they happen
- **Rich History**: Full conversation and command history tracking
- **Interactive Mode**: Engage in a conversation with the assistant
- **Security Checks**: Protection against potentially dangerous commands
- **Command Interruption**: Safely interrupt long-running commands

## Installation

1. Clone this repository to your WSL environment:

```bash
cd /home/benau/projects
git clone https://github.com/yourusername/openai-assistant-improved.git
cd openai-assistant-improved
```

2. Run the setup script:

```bash
./setup.sh
```

The setup script will:
- Check for Python and install it if needed
- Install required Python packages
- Create necessary directories
- Set up the SQLite database
- Configure your OpenAI API key

## Usage

### Interactive Mode

Run the assistant in interactive mode:

```bash
python main.py --interactive --base-prompt "You are an assistant that helps with creating and executing shell commands in WSL."
```

In interactive mode, you can:
- Type natural language prompts for the assistant to process
- Use special commands like `help`, `clear`, `sessions`, etc.
- Watch commands executing in real-time with colorized output

### Special Commands

While in interactive mode, you can use these special commands:

- `help`: Show help information
- `exit` or `quit`: Exit the program
- `clear`: Clear the screen
- `sessions`: List available sessions
- `switch <id>`: Switch to a different session
- `history`: Show history of current session
- `context`: Show current context summary
- `reset`: Reset the context but stay in the same session
- `export <file>`: Export current session to a file

### Single Prompt Mode

Run the assistant with a single prompt:

```bash
python main.py --prompt "Create a Python script that lists all files in the current directory."
```

### Session Management

Continue a previous session:

```bash
python main.py --interactive --session 20250504_123456
```

List available sessions:

```bash
python main.py --list-sessions
```

Export a session to a file:

```bash
python main.py --export-session 20250504_123456
```

## Advanced Options

### Command-line Arguments

- `--base-prompt`, `-b`: The base prompt to include in every call
- `--prompt`, `-p`: Initial prompt to start with
- `--interactive`, `-i`: Run in interactive mode
- `--session`, `-s`: Specify a session ID to continue
- `--list-sessions`, `-l`: List available sessions
- `--session-name`, `-n`: Name for a new session
- `--max-calls`, `-m`: Maximum number of API calls to make (default: 20)
- `--auto-loop`, `-a`: Automatically loop using the same prompt
- `--loop-delay`, `-d`: Delay between loops in seconds (default: 2)
- `--history-limit`: Maximum number of past calls to include in context (default: 10)
- `--clear-context`, `-c`: Start with a fresh context
- `--system-info`: Override the default system information
- `--export-session`, `-e`: Export a session to a JSON file
- `--temperature`, `-t`: Temperature for OpenAI API (0.0-1.0)
- `--verbose`, `-v`: Enable verbose output

## How It Works

### Improved Architecture

1. **Context Management**:
   - SQLite database for persistent storage
   - Session-based conversation tracking
   - Advanced context retrieval with customizable limits

2. **Real-time Command Execution**:
   - Commands are executed with live streaming output
   - Color-coded output for better readability
   - Progress indication for long-running commands

3. **Enhanced User Experience**:
   - Rich interactive mode with special commands
   - Clear visual separation between prompts, responses, and commands
   - Command history and editing via readline

4. **OpenAI Integration**:
   - Automatic retry logic for API failures
   - Configurable temperature and token settings
   - Structured message formatting for better context

## Project Structure

- `main.py`: Main entry point and interactive loop
- `context_handler.py`: SQLite-based conversation context manager
- `command_executor.py`: Real-time command execution module
- `openai_handler.py`: OpenAI API integration with error handling
- `setup.sh`: Installation and configuration script
- `logs/`: Directory for log files (if enabled)
- `data/`: Directory for SQLite database and other data files

## Example Workflows

### Example 1: Create and Test a Python Script

```
> I need a Python script that reads a CSV file and prints the sum of values in the second column.

[Assistant creates a Python script with detailed explanation]

[Commands execute in real-time with output:]
> Creating example CSV file for testing...
> Writing Python script...
> Testing script with example data...
> Sum of values in second column: 123.45

> Now modify the script to calculate the average instead of sum.

[Assistant modifies the script and runs it again]
```

### Example 2: System Administration Tasks

```
> Check disk usage and list the 5 largest files in the current directory

[Assistant analyzes the request and creates appropriate commands]

[Commands execute with real-time output:]
> df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   45G   55G  45% /

> find . -type f -exec du -h {} \; | sort -rh | head -n 5
120M    ./large_dataset.csv
75M     ./backup.tar.gz
50M     ./images/photo.jpg
32M     ./videos/demo.mp4
28M     ./logs/app.log
```

### Example 3: Multi-step Development Project

```
> Let's create a simple Flask web application that allows users to upload files.

[Assistant guides through multiple steps, with each command executing in real-time]

> Now let's test the application.

[Commands execute, starting the Flask server]

> The application is running! Access it at http://127.0.0.1:5000/
```

## Security Considerations

The command executor includes security checks to prevent potentially dangerous commands:

- Filtering out commands that could damage the system (e.g., `rm -rf /`)
- Interactive confirmation for suspicious commands
- Execution timeout to prevent hanging operations

## Future Improvements

Potential enhancements for future versions:

1. Web interface for easier interaction
2. Support for executing code in multiple languages (Python, JavaScript, etc.)
3. Integration with other AI models and APIs
4. Built-in file editing capabilities
5. Advanced session management with tagging and search
6. Cloud synchronization of sessions

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

This project is an improvement on the original OpenAI Assistant project, with inspiration from AutoGPT and similar tools.
