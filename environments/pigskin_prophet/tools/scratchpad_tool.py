"""
Simple scratchpad tool for persistent notes across weeks.
"""

import json
import os
import re
from typing import Dict, Any
import tiktoken

def _safe_model_identifier(name: str | None) -> str:
    """Return a filesystem-safe identifier for a model/scratchpad name.

    - Falls back to env defaults if name is empty or "default".
    - Replaces path separators and unsafe chars with underscores.
    - Trims repeated underscores and strips leading/trailing underscores.
    """
    # Prefer explicit name, else fall back to env vars
    if not name or name == "default":
        name = (
            os.getenv("PIGSKIN_SCRATCHPAD_MODEL")
            or os.getenv("SCRATCHPAD_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "default"
        )

    # Normalize to string
    name = str(name)

    # Replace slashes and backslashes first to avoid directories
    name = name.replace("/", "_").replace("\\", "_")

    # Replace any non word, dot, or dash characters with underscore
    name = re.sub(r"[^\w.\-]+", "_", name)

    # Collapse consecutive underscores and strip
    name = re.sub(r"_+", "_", name).strip("_")

    # Safety: final fallback
    return name or "default"


class ScratchpadTool:
    """Persistent scratchpad for models to track insights."""
    
    def __init__(self, model_name: str, season: int = 2025, max_tokens: int = 20000):
        # Resolve and sanitize model identifier for storage
        self.model_name = _safe_model_identifier(model_name)
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Storage path
        self.storage_dir = f"./scratchpads/{season}"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.filepath = f"{self.storage_dir}/{self.model_name}.json"
        
        # Load existing or create new
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load scratchpad from disk."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {"content": "", "week_updated": 0}
    
    def _save(self):
        """Save scratchpad to disk."""
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def read(self) -> str:
        """Read the scratchpad content."""
        return self.data["content"]
    
    def search(self, query: str) -> str:
        """Search scratchpad for a term and return surrounding context."""
        content = self.data["content"].lower()
        query_lower = query.lower()
        
        if query_lower not in content:
            return f"No mentions of '{query}' found"
        
        # Find and return the line containing the query + surrounding lines
        lines = self.data["content"].split('\n')
        matches = []
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Get context: 1 line before and after
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context = '\n'.join(lines[start:end])
                matches.append(context)
        
        if not matches:
            return f"No mentions of '{query}' found"
        
        return f"Found {len(matches)} mention(s) of '{query}':\n\n" + "\n---\n".join(matches[:3])  # Return first 3 matches
    
    def write(self, content: str, append: bool = True, week: int = None) -> Dict[str, Any]:
        """Write to scratchpad.
        
        Args:
            content: Text to write
            append: If True, append to existing. If False, replace all.
            week: Current week number
            
        Returns:
            Status with token count
        """
        if append and self.data["content"]:
            new_content = self.data["content"] + "\n\n" + content
        else:
            new_content = content
        
        # Check token limit
        token_count = len(self.tokenizer.encode(new_content))
        if token_count > self.max_tokens:
            return {
                "success": False,
                "message": f"Exceeds {self.max_tokens} token limit ({token_count} tokens)",
                "token_count": token_count
            }
        
        # Update and save
        self.data["content"] = new_content
        if week:
            self.data["week_updated"] = week
        self._save()
        
        return {
            "success": True,
            "token_count": token_count,
            "tokens_remaining": self.max_tokens - token_count
        }
    
    def stats(self) -> Dict[str, Any]:
        """Get scratchpad statistics."""
        content = self.data["content"]
        token_count = len(self.tokenizer.encode(content)) if content else 0
        
        return {
            "model": self.model_name,
            "token_count": token_count,
            "tokens_remaining": self.max_tokens - token_count,
            "last_week_updated": self.data.get("week_updated", 0),
            "has_content": bool(content)
        }

# Global scratchpad instance - will be set by set_current_model()
_current_scratchpad = None

def set_current_model(model_name: str):
    """Set the current model for scratchpad operations.
    Call this before evaluating each model."""
    global _current_scratchpad
    _current_scratchpad = ScratchpadTool(model_name)

def _get_scratchpad() -> ScratchpadTool:
    """Get the current scratchpad instance."""
    global _current_scratchpad
    if _current_scratchpad is None:
        # Fallback to default if not set
        _current_scratchpad = ScratchpadTool("default")
    return _current_scratchpad

# Simple wrapper functions for Verifiers
def read_scratchpad() -> str:
    """Read scratchpad content for the current model."""
    tool = _get_scratchpad()
    return tool.read()

def search_scratchpad(query: str) -> str:
    """Search scratchpad for a term and get surrounding context.
    
    Args:
        query: Term to search for
    
    Returns:
        Up to 3 matches with surrounding context
    """
    tool = _get_scratchpad()
    return tool.search(query)

def write_scratchpad(content: str, append: bool = True) -> Dict[str, Any]:
    """Write to scratchpad for the current model.
    
    Args:
        content: Text to write
        append: If True, append. If False, replace all.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    # Calculate current week for tracking
    season_start = datetime(2025, 9, 4, tzinfo=ZoneInfo('America/Los_Angeles'))
    current_date = datetime.now(ZoneInfo('America/Los_Angeles'))
    
    if current_date < season_start:
        week = 1
    else:
        days_since_start = (current_date - season_start).days
        week = min((days_since_start // 7) + 1, 18)
    
    tool = _get_scratchpad()
    return tool.write(content, append, week)

def scratchpad_stats() -> Dict[str, Any]:
    """Get scratchpad statistics for the current model."""
    tool = _get_scratchpad()
    return tool.stats()
