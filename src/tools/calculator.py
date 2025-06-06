from langchain_core.tools import tool

@tool  
def calculator(expression: str) -> str:
    """Evaluate mathematical expressions."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"
