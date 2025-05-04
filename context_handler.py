"""
Context handler for the OpenAI Assistant Project.
"""
import os
import json
import datetime
import sqlite3
from typing import List, Dict, Any, Optional
import time

class ConversationContext:
    """
    Manages the context for conversations with the OpenAI API.
    Uses SQLite to store context data for better persistence and retrieval.
    """
    def __init__(self, db_path: str = "data/conversation_context.db"):
        """
        Initialize the context handler.
        
        Args:
            db_path (str): Path to the SQLite database
        """
        self.db_path = db_path
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                start_time TEXT,
                last_updated TEXT,
                system_info TEXT,
                base_prompt TEXT
            )
            ''')
            
            # Create messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                call_number INTEGER,
                timestamp TEXT,
                role TEXT,
                content TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
            
            # Create commands table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                message_id INTEGER,
                command_text TEXT,
                output TEXT,
                exit_code INTEGER,
                execution_time REAL,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (message_id) REFERENCES messages (message_id)
            )
            ''')
            
            # Create tags table for extensible metadata
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                message_id INTEGER,
                command_id INTEGER,
                key TEXT,
                value TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (message_id) REFERENCES messages (message_id),
                FOREIGN KEY (command_id) REFERENCES commands (command_id)
            )
            ''')
            
            conn.commit()
    
    def create_session(self, system_info: str, base_prompt: str, name: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            system_info (str): System information
            base_prompt (str): Base prompt for the session
            name (str, optional): Name for the session
            
        Returns:
            str: The session ID
        """
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        current_time = datetime.datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, name or f"Session {session_id}", current_time, current_time, system_info, base_prompt)
            )
            conn.commit()
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, call_number: int) -> int:
        """
        Add a message to the conversation.
        
        Args:
            session_id (str): The session ID
            role (str): The role (system, user, assistant)
            content (str): The message content
            call_number (int): The call number
            
        Returns:
            int: The message ID
        """
        current_time = datetime.datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update session last_updated time
            cursor.execute(
                "UPDATE sessions SET last_updated = ? WHERE session_id = ?",
                (current_time, session_id)
            )
            
            # Insert message
            cursor.execute(
                "INSERT INTO messages (session_id, call_number, timestamp, role, content) VALUES (?, ?, ?, ?, ?)",
                (session_id, call_number, current_time, role, content)
            )
            
            message_id = cursor.lastrowid
            conn.commit()
        
        return message_id
    
    def add_command(self, session_id: str, message_id: int, command_text: str, 
                   output: str, exit_code: int, execution_time: float) -> int:
        """
        Add a command execution record.
        
        Args:
            session_id (str): The session ID
            message_id (int): The message ID
            command_text (str): The command text
            output (str): The command output
            exit_code (int): The exit code
            execution_time (float): The execution time in seconds
            
        Returns:
            int: The command ID
        """
        current_time = datetime.datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO commands (session_id, message_id, command_text, output, exit_code, execution_time, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, message_id, command_text, output, exit_code, execution_time, current_time)
            )
            
            command_id = cursor.lastrowid
            conn.commit()
        
        return command_id
    
    def add_tag(self, session_id: str, key: str, value: str, message_id: Optional[int] = None, 
               command_id: Optional[int] = None) -> int:
        """
        Add a tag for metadata.
        
        Args:
            session_id (str): The session ID
            key (str): The tag key
            value (str): The tag value
            message_id (int, optional): The message ID
            command_id (int, optional): The command ID
            
        Returns:
            int: The tag ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tags (session_id, message_id, command_id, key, value) VALUES (?, ?, ?, ?, ?)",
                (session_id, message_id, command_id, key, value)
            )
            
            tag_id = cursor.lastrowid
            conn.commit()
        
        return tag_id
    
    def get_session_messages(self, session_id: str, limit: Optional[int] = None, 
                            offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages for a session.
        
        Args:
            session_id (str): The session ID
            limit (int, optional): Maximum number of messages to retrieve
            offset (int, optional): Offset for pagination
            
        Returns:
            List[Dict[str, Any]]: List of message dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM messages WHERE session_id = ? ORDER BY call_number DESC"
            params = [session_id]
            
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            messages = []
            for row in results:
                message = dict(row)
                
                # Get commands for this message
                cursor.execute(
                    "SELECT * FROM commands WHERE message_id = ?",
                    (message["message_id"],)
                )
                commands = [dict(cmd) for cmd in cursor.fetchall()]
                message["commands"] = commands
                
                # Get tags for this message
                cursor.execute(
                    "SELECT key, value FROM tags WHERE message_id = ?",
                    (message["message_id"],)
                )
                tags = {row["key"]: row["value"] for row in cursor.fetchall()}
                message["tags"] = tags
                
                messages.append(message)
        
        return messages
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> str:
        """
        Get formatted conversation history for a session.
        
        Args:
            session_id (str): The session ID
            limit (int, optional): Maximum number of messages to include
            
        Returns:
            str: Formatted conversation history
        """
        messages = self.get_session_messages(session_id, limit)
        
        # Organize by call number
        call_data = {}
        for message in messages:
            call_number = message["call_number"]
            if call_number not in call_data:
                call_data[call_number] = {
                    "user": None,
                    "assistant": None,
                    "commands": []
                }
            
            if message["role"] == "user":
                call_data[call_number]["user"] = message
            elif message["role"] == "assistant":
                call_data[call_number]["assistant"] = message
                
            # Add commands
            for cmd in message.get("commands", []):
                call_data[call_number]["commands"].append(cmd)
        
        # Format as string
        history_parts = []
        for call_number, data in sorted(call_data.items()):
            history_parts.append(f"## CALL #{call_number}")
            
            if data["user"]:
                history_parts.append("### Prompt Given:")
                history_parts.append(data["user"]["content"])
            
            if data["assistant"]:
                history_parts.append("### Assistant Response:")
                history_parts.append(data["assistant"]["content"])
            
            if data["commands"]:
                history_parts.append("### Commands Executed:")
                for cmd in data["commands"]:
                    history_parts.append(f"Command: {cmd['command_text']}")
                    history_parts.append(f"Output: {cmd['output']}")
                    history_parts.append(f"Exit Code: {cmd['exit_code']}")
                    history_parts.append(f"Execution Time: {cmd['execution_time']:.2f}s")
            
            history_parts.append("---")
        
        return "\n".join(history_parts)
    
    def get_sessions_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all sessions.
        
        Returns:
            List[Dict[str, Any]]: List of session dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages, commands, and tags.
        
        Args:
            session_id (str): The session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete tags
                cursor.execute("DELETE FROM tags WHERE session_id = ?", (session_id,))
                
                # Delete commands
                cursor.execute("DELETE FROM commands WHERE session_id = ?", (session_id,))
                
                # Delete messages
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                
                # Delete session
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting session: {str(e)}")
            return False
    
    def get_openai_context(self, session_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get context for OpenAI API in the format expected by the API.
        
        Args:
            session_id (str): The session ID
            limit (int, optional): Maximum number of messages to include
            
        Returns:
            Dict[str, Any]: OpenAI API context
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            session = dict(cursor.fetchone())
            
            # Get messages
            messages = self.get_session_messages(session_id, limit)
            
            # Format for OpenAI
            openai_messages = [
                {"role": "system", "content": f"# === SYSTEM INFORMATION ===\n{session['system_info']}\n# === BASE USER PROMPT ===\nPrompt: {session['base_prompt']}\n# === CONVERSATION HISTORY ===\n{self.get_conversation_history(session_id, limit)}"}
            ]
            
            # Add messages in chronological order (older first)
            for message in reversed(messages):
                if message["role"] in ["user", "assistant"]:
                    openai_messages.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
        
        return {
            "session": session,
            "messages": openai_messages
        }
