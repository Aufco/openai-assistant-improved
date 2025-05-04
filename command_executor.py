#!/bin/bash
# Project creation script for OpenAI Assistant Improved

# Check if project name is provided
if [ -z "$1" ]; then
    echo "Usage: ./create_project.sh <project_name>"
    exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="/home/benau/projects/$PROJECT_NAME"

# Create project directory
echo "Creating project directory at $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create basic structure
mkdir -p logs data tests gitignore

# Create basic files
touch README.md
touch .env

# Create .gitignore
echo -e ".env\n__pycache__/\n*.pyc\ngitignore/" > .gitignore

# Create main.py
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Main entry point for the project.
"""

def main():
    """Main function."""
    print("Project initialized!")

if __name__ == "__main__":
    main()
EOF

# Make main.py executable
chmod +x main.py

# Create requirements.txt
cat > requirements.txt << 'EOF'
openai
python-dotenv
tqdm
colorama
requests
EOF

# Create setup.sh
cat > setup.sh << 'EOF'
#!/bin/bash
# Setup script

echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages

echo "Setup complete!"
EOF

chmod +x setup.sh

# Initialize git repository
git init -b main

# Create initial commit
git add .
git commit -m "Initial project setup"

echo "Project $PROJECT_NAME created successfully at $PROJECT_DIR"
echo "To install dependencies, run: cd $PROJECT_DIR && ./setup.sh"
