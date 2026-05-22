import os
import sys
import requests
from fastmcp import FastMCP

# Add the parent directory to system path to import the orchestrator module
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from orchestrator.llm import LLMHelper

# Create the MCP server named "WebResearchServer"
mcp = FastMCP("WebResearchServer")

def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Perform a web search using duckduckgo-search library."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            # Format results to uniform dict
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
            return formatted
    except Exception as e:
        print(f"DuckDuckGo search error: {e}", file=sys.stderr)
        return []

def search_wikipedia(query: str, max_results: int = 3) -> list[dict]:
    """Fallback search using Wikipedia's API."""
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1
        }
        headers = {"User-Agent": "StudyMCP-Assistant/1.0 (contact: user@example.com)"}
        r = requests.get(search_url, params=params, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            search_results = data.get("query", {}).get("search", [])
            results = []
            for item in search_results[:max_results]:
                title = item.get("title")
                snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                href = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                results.append({
                    "title": f"{title} (Wikipedia)",
                    "href": href,
                    "body": snippet
                })
            return results
    except Exception as e:
        print(f"Wikipedia search fallback error: {e}", file=sys.stderr)
    return []

@mcp.tool()
def search_web(query: str) -> str:
    """
    Search the web for a query and return formatted results.
    
    Args:
        query: The search query string.
    """
    if not query:
        return "Error: Query cannot be empty."
        
    print(f"Searching web for: '{query}'...", file=sys.stderr)
    
    # Try DuckDuckGo
    results = search_duckduckgo(query, max_results=5)
    
    # Fallback to Wikipedia if DDG returns nothing
    if not results:
        print("DuckDuckGo search yielded no results. Trying Wikipedia fallback...", file=sys.stderr)
        results = search_wikipedia(query, max_results=3)
        
    if not results:
        return f"No results found on the web for '{query}'."
        
    # Format the results into a readable string
    output = []
    for idx, r in enumerate(results, 1):
        output.append(f"{idx}. **{r['title']}**")
        output.append(f"   URL: {r['href']}")
        output.append(f"   Snippet: {r['body']}\n")
        
    return "\n".join(output)

@mcp.tool()
def summarize_results(query: str) -> str:
    """
    Search the web for a query and summarize the results into key points.
    
    Args:
        query: The search query to summarize.
    """
    search_data = search_web(query)
    if search_data.startswith("No results found") or search_data.startswith("Error"):
        return f"Could not summarize search results: {search_data}"
        
    # Set up LLMHelper and generate summary
    try:
        llm = LLMHelper()
        prompt = (
            f"Please summarize the following web search results for the query '{query}' into key, structured bullet points. "
            f"Focus on educational facts, scientific validity, or historical context depending on the subject.\n\n"
            f"SEARCH RESULTS:\n{search_data}"
        )
        system_instruction = "You are a research summarizer. Distill search results into clear, concise, and academic summary points."
        summary = llm.generate(prompt=prompt, system_instruction=system_instruction)
        return summary
    except Exception as e:
        return f"Error generating summary via LLM: {e}\n\nRaw search results:\n{search_data}"

if __name__ == "__main__":
    mcp.run()
