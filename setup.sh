#!/bin/bash

# Improved Setup Script for OpenAI Assistant Project
echo -e "\033[1;36m"
cat << "EOF"
┌───────────────────────────────────────────────┐
│     OPENAI ASSISTANT WITH COMMAND EXECUTION    │
│                   SETUP SCRIPT                 │
└───────────────────────────────────────────────┘
EOF
echo -e "\033[0m"

# Check if Python is installed
echo -e "\033[1;33mChecking Python installation...\033[0m"
if ! command -v python3 &>/dev/null; then
    echo -e "\033[1;31mPython 3 is not installed. Installing...\033[0m"
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
else
    python_version=$(python3 --version)
    echo -e "\033[1;32m✓ ${python_version} is installed.\033[0m"
fi

# Install required Python packages
echo -e "\033[1;33mInstalling required Python packages...\033[0m"
pip3 install openai python-dotenv requests tqdm colorama readline sqlite3 --break-system-packages

# Create project structure
echo -e "\033[1;33mSetting up project structure...\033[0m"
mkdir -p logs
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\033[1;33mCreating .env file...\033[0m"
    read -p "Enter your OpenAI API Key: " api_key
    echo "OPENAI_API_KEY=${api_key}" > .env
    echo "OPENAI_MODEL=gpt-4-turbo" >> .env
    echo -e "\033[1;32m✓ .env file created with API key.\033[0m"
else
    echo -e "\033[1;32m✓ .env file already exists.\033[0m"
fi

# Set execution permissions
echo -e "\033[1;33mSetting executable permissions...\033[0m"
chmod +x main.py
chmod +x setup.sh

# Create an example command for testing
echo -e "\033[1;33mCreating test file...\033[0m"
cat > test_command.txt << 'EOF'
echo "Hello from the OpenAI Assistant!"
ls -la
echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "System information: $(uname -a)"
EOF
chmod +x test_command.txt
echo -e "\033[1;32m✓ Created test_command.txt for testing.\033[0m"

# Create database if it doesn't exist
echo -e "\033[1;33mInitializing database...\033[0m"
python3 -c "from context_handler import ConversationContext; ConversationContext()"
echo -e "\033[1;32m✓ Database initialized.\033[0m"

echo -e "\033[1;36m"
cat << "EOF"
┌───────────────────────────────────────────────┐
│               SETUP COMPLETE!                 │
│                                               │
│  Run the assistant with:                      │
│  python3 main.py --interactive                │
│                                               │
│  Or try a single command:                     │
│  python3 main.py --prompt "Create a hello     │
│  world script in Python"                      │
└───────────────────────────────────────────────┘
EOF
echo -e "\033[0m"

echo -e "\033[1;33mWould you like to test the installation? (y/n)\033[0m"
read test_installation

if [[ $test_installation == "y" ]]; then
    echo -e "\033[1;36mTesting installation...\033[0m"
    python3 -c "import openai, sqlite3, readline, json, colorama; print('All modules imported successfully!')"
    python3 main.py --prompt "Say hello and tell me the current date" --max-calls 1
fi

echo -e "\033[1;32mSetup complete! Enjoy your improved OpenAI Assistant!\033[0m"
