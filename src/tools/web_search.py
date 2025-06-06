from langchain_core.tools import tool
import requests
from urllib.parse import quote_plus
import json

@tool
def web_search(query: str) -> str:
    """Search the web for current information using DuckDuckGo."""
    try:
        # Use DuckDuckGo Instant Answer API (free, no API key required)
        encoded_query = quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1&no_html=1&skip_disambig=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant information
        results = []
        
        # Get abstract/summary
        if data.get('Abstract'):
            results.append(f"Summary: {data['Abstract']}")
            # If there's an abstract URL, include it
            if data.get('AbstractURL'):
                results.append(f"Source URL: {data['AbstractURL']}")
        
        # Get definition if available
        if data.get('Definition'):
            results.append(f"Definition: {data['Definition']}")
        
        # Get related topics
        if data.get('RelatedTopics'):
            topics = []
            for topic in data['RelatedTopics'][:3]:  # Limit to first 3
                if isinstance(topic, dict) and topic.get('Text'):
                    topics.append(topic['Text'])
            if topics:
                results.append(f"Related information: {'; '.join(topics)}")
        
        # Get answer if available
        if data.get('Answer'):
            results.append(f"Direct answer: {data['Answer']}")
        
        # Check for infobox data (often contains official URLs)
        if data.get('Infobox') and data['Infobox'].get('content'):
            for item in data['Infobox']['content'][:2]:  # Limit to first 2
                if item.get('data_type') == 'website' and item.get('value'):
                    results.append(f"Official website: {item['value']}")
        
        if results:
            return f"Search results for '{query}':\n" + "\n\n".join(results)
        else:
            # Provide helpful suggestions for common documentation queries
            if 'doc' in query.lower() or 'documentation' in query.lower():
                return f"No specific results found for '{query}'. For documentation searches, try:\n- Searching directly on the official website\n- Adding 'official' to your search query\n- Checking the project's GitHub repository"
            else:
                return f"No specific results found for '{query}'. Try rephrasing your search query."
            
    except requests.RequestException as e:
        return f"Error searching for '{query}': Network error - {str(e)}"
    except json.JSONDecodeError:
        return f"Error searching for '{query}': Invalid response format"
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"
