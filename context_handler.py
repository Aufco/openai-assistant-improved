"""
Improved OpenAI API handler for the Assistant Project.
"""
import os
import openai
from typing import List, Dict, Any, Optional
import json

# Try to load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set default model
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# Configure OpenAI API
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def make_openai_request(messages, model=None, temperature=0.7, max_tokens=2048, timeout=60, retry_attempts=3):
    """
    Make a request to the OpenAI API with enhanced error handling and retry logic.
    
    Args:
        messages (List[Dict[str, str]]): Messages for the API
        model (str, optional): The model to use
        temperature (float, optional): Temperature for sampling
        max_tokens (int, optional): Maximum tokens in the response
        timeout (int, optional): Timeout in seconds
        retry_attempts (int, optional): Number of retry attempts
        
    Returns:
        str: The response text
    """
    if not openai.api_key:
        raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")
    
    model = model or DEFAULT_MODEL
    
    # Retry loop
    for attempt in range(retry_attempts):
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                timeout=timeout
            )
            
            return response.choices[0].message.content
        
        except openai.APIConnectionError as e:
            if attempt < retry_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"API connection error, retrying in {wait_time} seconds... ({attempt+1}/{retry_attempts})")
                time.sleep(wait_time)
            else:
                return f"Error connecting to OpenAI API after {retry_attempts} attempts: {str(e)}"
        
        except openai.RateLimitError as e:
            if attempt < retry_attempts - 1:
                wait_time = 10 + 5 * attempt  # Longer wait for rate limits
                print(f"Rate limit exceeded, retrying in {wait_time} seconds... ({attempt+1}/{retry_attempts})")
                time.sleep(wait_time)
            else:
                return f"OpenAI API rate limit exceeded after {retry_attempts} attempts: {str(e)}"
        
        except openai.BadRequestError as e:
            # For bad requests, we don't retry as they're likely to fail again
            return f"Bad request to OpenAI API: {str(e)}"
        
        except Exception as e:
            if attempt < retry_attempts - 1:
                wait_time = 2 ** attempt
                print(f"Error with OpenAI API, retrying in {wait_time} seconds... ({attempt+1}/{retry_attempts})")
                time.sleep(wait_time)
            else:
                return f"Error with OpenAI API after {retry_attempts} attempts: {str(e)}"

def format_message_with_system_info(system_info, base_prompt, conversation_history):
    """
    Format the system message with system information and base prompt.
    
    Args:
        system_info (str): System information
        base_prompt (str): Base prompt
        conversation_history (str): Formatted conversation history
        
    Returns:
        str: Formatted system message
    """
    return f"""# === SYSTEM INFORMATION ===
{system_info}

# === BASE USER PROMPT ===
{base_prompt}

# === CONVERSATION HISTORY ===
{conversation_history}

As an AI assistant, your goal is to help the user by:
1. Providing relevant information based on the query
2. Generating shell commands that can be executed in the WSL environment
3. Understanding the output of previous commands and using it to provide further assistance

Always provide commands within <command></command> tags.
Focus on being helpful, clear, and concise in your responses.
"""

def get_available_models():
    """
    Get a list of available models from OpenAI.
    
    Returns:
        List[str]: List of available model IDs
    """
    try:
        models = openai.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Error getting available models: {str(e)}")
        return [DEFAULT_MODEL, "gpt-4", "gpt-3.5-turbo"]
