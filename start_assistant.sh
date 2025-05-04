#!/bin/bash
# Script to start the OpenAI Assistant with common configurations

# Define color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Display banner
echo -e "${BLUE}"
cat << "EOF"
┌───────────────────────────────────────────────┐
│     OPENAI ASSISTANT WITH COMMAND EXECUTION    │
│                                               │
│  An AI assistant that executes commands and   │
│  provides real-time feedback                  │
└───────────────────────────────────────────────┘
EOF
echo -e "${NC}"

# Parse command line arguments
INTERACTIVE=false
RESET_LOGS=false
SESSION=""
PROMPT=""
BASE_PROMPT=""
MAX_CALLS=20
TEMPERATURE=0.7

# Check for common help flags
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo -e "${YELLOW}Usage: ./start_assistant.sh [options]${NC}"
    echo "Options:"
    echo "  --interactive, -i           Start in interactive mode"
    echo "  --reset, -r                 Reset logs and start fresh"
    echo "  --session=ID, -s ID         Continue a specific session"
echo "  --prompt=TEXT, -p TEXT      Provide an initial prompt"
echo "  --base-prompt=TEXT, -b TEXT   Set the base prompt for all interactions"
echo "  --max-calls=N, -m N          Maximum number of API calls (default: 20)"
echo "  --temp=N, -t N               Temperature setting (0.0-1.0, default: 0.7)"
echo "  --list-sessions, -l          List available sessions"

echo -e "${GREEN}Examples:${NC}"
echo "  ./start_assistant.sh --interactive"
echo "  ./start_assistant.sh --prompt=\"Create a hello world script\""
echo "  ./start_assistant.sh --session=20250504_123456"
exit 0
fi

# Parse arguments
for i in "$@"; do
    case $i in
        --interactive|-i)
            INTERACTIVE=true
            shift
            ;;
        --reset|-r)
            RESET_LOGS=true
            shift
            ;;
        --session=*|-s)
            if [[ $i == --session=* ]]; then
                SESSION="${i#*=}"
            else
                SESSION="$2"
                shift
            fi
            shift
            ;;
        --prompt=*|-p)
            if [[ $i == --prompt=* ]]; then
                PROMPT="${i#*=}"
            else
                PROMPT="$2"
                shift
            fi
            shift
            ;;
        --base-prompt=*|-b)
            if [[ $i == --base-prompt=* ]]; then
                BASE_PROMPT="${i#*=}"
            else
                BASE_PROMPT="$2"
                shift
            fi
            shift
            ;;
        --max-calls=*|-m)
            if [[ $i == --max-calls=* ]]; then
                MAX_CALLS="${i#*=}"
            else
                MAX_CALLS="$2"
                shift
            fi
            shift
            ;;
        --temp=*|-t)
            if [[ $i == --temp=* ]]; then
                TEMPERATURE="${i#*=}"
            else
                TEMPERATURE="$2"
                shift
            fi
            shift
            ;;
        --list-sessions|-l)
            echo -e "${YELLOW}Listing available sessions:${NC}"
            python3 main.py --list-sessions
            exit 0
            ;;
        *)
            # Unknown option
            echo "Unknown option: $i"
            exit 1
            ;;
    esac
done

# Set default base prompt if not provided
if [ -z "$BASE_PROMPT" ]; then
    BASE_PROMPT="You are an AI assistant that helps with executing commands in WSL. Your responses should be concise and focused on the task at hand. Always provide shell commands within <command></command> tags when appropriate."
fi

# Build command arguments
ARGS=""

if [ "$INTERACTIVE" = true ]; then
    ARGS="$ARGS --interactive"
fi

if [ "$RESET_LOGS" = true ]; then
    ARGS="$ARGS --reset-logs"
fi

if [ ! -z "$SESSION" ]; then
    ARGS="$ARGS --session $SESSION"
fi

if [ ! -z "$PROMPT" ]; then
    ARGS="$ARGS --prompt \"$PROMPT\""
fi

ARGS="$ARGS --base-prompt \"$BASE_PROMPT\" --max-calls $MAX_CALLS --temperature $TEMPERATURE"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${YELLOW}main.py not found. Make sure you're in the correct directory.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating a default one.${NC}"
    echo "OPENAI_API_KEY=" > .env
    echo "OPENAI_MODEL=gpt-4-turbo" >> .env
    echo -e "${YELLOW}Please edit the .env file to add your OpenAI API key.${NC}"
fi

# Check if API key is set
if ! grep -q "OPENAI_API_KEY=.*[^[:space:]]" .env; then
    echo -e "${YELLOW}OpenAI API key not set in .env file.${NC}"
    read -p "Enter your OpenAI API key: " API_KEY
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$API_KEY/" .env
fi

# Start the assistant
echo -e "${GREEN}Starting OpenAI Assistant...${NC}"
echo -e "${BLUE}Parameters:${NC}"
echo "  Interactive mode: $INTERACTIVE"
echo "  Reset logs: $RESET_LOGS"
if [ ! -z "$SESSION" ]; then
    echo "  Session: $SESSION"
fi
if [ ! -z "$PROMPT" ]; then
    echo "  Prompt: $PROMPT"
fi
echo "  Max calls: $MAX_CALLS"
echo "  Temperature: $TEMPERATURE"
echo -e "${GREEN}Executing: python3 main.py $ARGS${NC}"
echo ""

# Execute the command
eval "python3 main.py $ARGS"
