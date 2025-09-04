"""
Simple scratchpad tool for persistent notes across weeks.
"""

import json
import os
from typing import Dict, Any
import tiktoken

class ScratchpadTool:
    """Persistent scratchpad for models to track insights."""
    
    def __init__(self, model_name: str, season: int = 2025, max_tokens: int = 20000):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Storage path
        self.storage_dir = f"./scratchpads/{season}"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.filepath = f"{self.storage_dir}/{model_name}.json"
        
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

# Simple wrapper functions for Verifiers
def read_scratchpad(model_name: str = "default") -> str:
    """Read scratchpad content."""
    tool = ScratchpadTool(model_name)
    return tool.read()

def search_scratchpad(query: str, model_name: str = "default") -> str:
    """Search scratchpad for a term and get surrounding context.
    
    Args:
        query: Term to search for
        model_name: Model identifier
    
    Returns:
        Up to 3 matches with surrounding context
    """
    tool = ScratchpadTool(model_name)
    return tool.search(query)

def write_scratchpad(content: str, 
                    append: bool = True, 
                    week: int = None,
                    model_name: str = "default") -> Dict[str, Any]:
    """Write to scratchpad.
    
    Args:
        content: Text to write
        append: If True, append. If False, replace all.
        week: Current week number
        model_name: Model identifier
    """
    tool = ScratchpadTool(model_name)
    return tool.write(content, append, week)

def scratchpad_stats(model_name: str = "default") -> Dict[str, Any]:
    """Get scratchpad statistics."""
    tool = ScratchpadTool(model_name)
    return tool.stats()