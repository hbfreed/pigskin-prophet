"""
Exa search tool for web research following Verifiers ToolEnv pattern.
Optimized for cost-effective keyword search with full text retrieval.
"""

import os
from typing import List, Dict
from exa_py import Exa
from dotenv import load_dotenv
import asyncio
from concurrent.futures import TimeoutError

load_dotenv()

# Initialize Exa client
exa_client = None

def _init_exa():
    """Initialize Exa client if not already initialized."""
    global exa_client
    if exa_client is None:
        api_key = os.getenv('EXA_API_KEY')
        if not api_key:
            return None
        exa_client = Exa(api_key)
    return exa_client

async def search_web_exa(
    query: str
) -> List[Dict]:
    """Search the web using Exa's search API.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with title, url, and summary content
    """
    include_domains = None
    exclude_domains = None  
    category = None
    try:
        # Initialize client
        client = _init_exa()
        if client is None:
            return [{"error": "EXA_API_KEY not found in environment variables"}]
        
        # Run search in executor to handle async properly
        loop = asyncio.get_event_loop()
        
        def _search():
            # Use keyword search type for cost efficiency ($2.50/1k vs $5/1k for neural)
            search_params = {
                "query": query,
                "type": "keyword",
                "num_results": 5,
                "text": False, 
                "highlights": False,
                "summary": True  # Get AI-generated summaries
            }
            
            # Add optional filters
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            if category:
                search_params["category"] = category
            
            # Execute search with content retrieval
            results = client.search_and_contents(**search_params)
            
            # Format results for model consumption
            formatted_results = []
            for result in results.results:
                formatted_results.append({
                    "title": result.title,
                    "url": result.url,
                    "summary": result.summary if hasattr(result, 'summary') and result.summary else "",
                    "published_date": result.published_date if hasattr(result, 'published_date') else None
                })
            
            return formatted_results
        
        # Run with timeout
        future = loop.run_in_executor(None, _search)
        results = await asyncio.wait_for(future, timeout=10.0)
        return results
        
    except TimeoutError:
        return [{"error": "Search timeout after 10 seconds"}]
    except Exception as e:
        return [{"error": f"Search error: {str(e)}"}]

def search_web_exa_sync(
    query: str
) -> List[Dict]:
    """Synchronous version of search_web_exa for compatibility.
    
    Uses keyword search ($2.50/1k) instead of neural ($5/1k) and retrieves
    summaries to provide focused content.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with title, url, and summary content
    """
    include_domains = None
    exclude_domains = None
    category = None
    try:
        # Initialize client
        client = _init_exa()
        if client is None:
            return [{"error": "EXA_API_KEY not found in environment variables"}]
        
        # Use keyword search type for cost efficiency
        search_params = {
            "query": query,
            "type": "keyword",  # Cost-optimized choice
            "num_results": 5,  # Hard-coded to prevent cheating
            "text": False,  # Skip full text
            "highlights": False,  # Skip highlights
            "summary": True  # Get AI-generated summaries ($1/1k)
        }
        
        # Add optional filters
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if category:
            search_params["category"] = category
        
        # Execute search with content retrieval
        results = client.search_and_contents(**search_params)
        
        # Format results for model consumption
        formatted_results = []
        for result in results.results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "summary": result.summary if hasattr(result, 'summary') and result.summary else "",
                "published_date": result.published_date if hasattr(result, 'published_date') else None
            })
        
        return formatted_results
        
    except Exception as e:
        return [{"error": f"Search error: {str(e)}"}]

# For Verifiers ToolEnv integration, export the async version by default
# ToolEnv can handle both sync and async functions
search_tool = search_web_exa