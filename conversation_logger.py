import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("ComfyUI_ComfyAssistant.logger")

LOG_DIR = os.path.join(os.path.dirname(__file__), "user_context", "logs")

def log_interaction(thread_id, user_message, assistant_response, tool_calls=None, errors=None):
    """
    Logs a single chat interaction to a JSONL file.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "thread_id": thread_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "tool_calls": tool_calls or [],
        "errors": errors or []
    }

    # Daily log file
    log_file = os.path.join(LOG_DIR, f"chat_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write chat log: {e}")

def log_tool_execution(thread_id, tool_name, params, result, success):
    """
    Specialized log for tool executions to track failures in templates or nodes.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "tool_execution",
        "thread_id": thread_id,
        "tool": tool_name,
        "params": params,
        "success": success,
        "result": result
    }
    
    log_file = os.path.join(LOG_DIR, f"tools_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write tool log: {e}")
