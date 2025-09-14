"""
Brave search tool for web research following Verifiers ToolEnv pattern.
Uses Brave Search API for web search with similar interface to exa_tool.
Based on official Brave Search API documentation.
"""

import os
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv
import asyncio
from concurrent.futures import TimeoutError

load_dotenv()

# Initialize Brave API key
brave_api_key = None

def _init_brave():
    """Initialize Brave API key if not already initialized."""
    global brave_api_key
    if brave_api_key is None:
        brave_api_key = os.getenv('BRAVE_API_KEY')
        if not brave_api_key:
            return None
    return brave_api_key

async def search_web_brave(
    query: str
) -> List[Dict]:
    """Search the web using Brave's Search API.
    
    Based on official Brave Search API documentation.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with title, url, and text content
    """
    include_domains = None
    exclude_domains = None
    category = None
    try:
        # Initialize API key
        api_key = _init_brave()
        if api_key is None:
            return [{"error": "BRAVE_API_KEY not found in environment variables"}]
        
        # Run search in executor to handle async properly
        loop = asyncio.get_event_loop()
        
        def _search():
            # Brave Search API endpoint (from official docs)
            url = "https://api.search.brave.com/res/v1/web/search"
            
            # Build query with domain filters if provided
            search_query = query
            if include_domains:
                # Use OR for multiple domains
                domain_query = " OR ".join([f"site:{domain}" for domain in include_domains])
                search_query = f"{query} ({domain_query})"
            if exclude_domains:
                # Add exclusions
                for domain in exclude_domains:
                    search_query += f" -site:{domain}"
            
            # Set up parameters based on official documentation
            params = {
                "q": search_query,
                "count": 5,  # Hard-coded to prevent cheating (same as exa_tool)
                "country": "us",
                "search_lang": "en",
                "safesearch": "moderate",
                "freshness": None  # Will be set based on category
            }
            
            # Add category-specific filters
            if category == "news":
                params["freshness"] = "pw"  # Past week for news
            elif category == "recent":
                params["freshness"] = "pd"  # Past day
            
            # Remove None values from params
            params = {k: v for k, v in params.items() if v is not None}
            
            # Headers as per official documentation
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }
            
            # Make the request
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Format results similar to exa_tool
            formatted_results = []
            
            # Process web results based on actual API response structure
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"][:5]:  # Limit to 5 results
                    # Combine description and extra snippets for more context
                    text_content = result.get("description", "")
                    
                    # Add extra snippets if available (provides more context)
                    if "extra_snippets" in result and result["extra_snippets"]:
                        snippets = " ... ".join(result["extra_snippets"])
                        text_content = f"{text_content}\n\nAdditional context: {snippets}"
                    
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "text": text_content,
                        "published_date": result.get("page_age", result.get("age", None))
                    })
            
            return formatted_results if formatted_results else [{"error": "No results found"}]
        
        # Run with timeout
        future = loop.run_in_executor(None, _search)
        results = await asyncio.wait_for(future, timeout=10.0)
        return results
        
    except TimeoutError:
        return [{"error": "Search timeout after 10 seconds"}]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return [{"error": "Invalid API key. Please check BRAVE_API_KEY in .env"}]
        elif e.response.status_code == 429:
            return [{"error": "Rate limit exceeded. Please wait and try again."}]
        else:
            return [{"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}]
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Search error: {str(e)}"}]

def search_web_brave_sync(
    query: str, 
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    category: Optional[str] = None
) -> List[Dict]:
    """Synchronous version of search_web_brave for compatibility.
    
    Uses Brave Search API to retrieve web search results with snippets.
    Based on official Brave Search API documentation.
    
    Args:
        query: Search query string
        include_domains: Optional list of domains to include in search
        exclude_domains: Optional list of domains to exclude from search
        category: Optional category filter (news, recent, etc.)
        
    Returns:
        List of search results with title, url, and text content
    """
    try:
        # Initialize API key
        api_key = _init_brave()
        if api_key is None:
            return [{"error": "BRAVE_API_KEY not found in environment variables"}]
        
        # Brave Search API endpoint (from official docs)
        url = "https://api.search.brave.com/res/v1/web/search"
        
        # Build query with domain filters if provided
        search_query = query
        if include_domains:
            # Use OR for multiple domains
            domain_query = " OR ".join([f"site:{domain}" for domain in include_domains])
            search_query = f"{query} ({domain_query})"
        if exclude_domains:
            # Add exclusions
            for domain in exclude_domains:
                search_query += f" -site:{domain}"
        
        # Set up parameters based on official documentation
        params = {
            "q": search_query,
            "count": 5,  # Hard-coded to prevent cheating (same as exa_tool)
            "country": "us",
            "search_lang": "en",
            "safesearch": "moderate",
            "freshness": None  # Will be set based on category
        }
        
        # Add category-specific filters
        if category == "news":
            params["freshness"] = "pw"  # Past week for news
        elif category == "recent":
            params["freshness"] = "pd"  # Past day
        
        # Remove None values from params
        params = {k: v for k, v in params.items() if v is not None}
        
        # Headers as per official documentation
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }
        
        # Make the request
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Format results similar to exa_tool
        formatted_results = []
        
        # Process web results based on actual API response structure
        if "web" in data and "results" in data["web"]:
            for result in data["web"]["results"][:5]:  # Limit to 5 results
                # Combine description and extra snippets for more context
                text_content = result.get("description", "")
                
                # Add extra snippets if available (provides more context)
                if "extra_snippets" in result and result["extra_snippets"]:
                    snippets = " ... ".join(result["extra_snippets"])
                    text_content = f"{text_content}\n\nAdditional context: {snippets}"
                
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "text": text_content,
                    "published_date": result.get("page_age", result.get("age", None))
                })
        
        return formatted_results if formatted_results else [{"error": "No results found"}]
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return [{"error": "Invalid API key. Please check BRAVE_API_KEY in .env"}]
        elif e.response.status_code == 429:
            return [{"error": "Rate limit exceeded. Please wait and try again."}]
        else:
            return [{"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}]
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Search error: {str(e)}"}]

# For Verifiers ToolEnv integration, export the async version by default
# ToolEnv can handle both sync and async functions
search_tool = search_web_brave