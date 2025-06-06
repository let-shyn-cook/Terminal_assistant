from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# Handle both relative and absolute imports
try:
    from .tools import web_search, calculator, list_directory, run_command, detect_system, get_system_info
except ImportError:
    from tools import web_search, calculator, list_directory, run_command, detect_system, get_system_info
import requests
import json

# Load environment variables from .env file
load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]
    conversation_summary: str

# Global conversation history for persistence
conversation_history = []
conversation_summary = ""

def summarize_conversation(messages: list) -> str:
    """Summarize the conversation to maintain context without storing all messages."""
    if len(messages) < 4:  # Don't summarize very short conversations
        return ""
    
    # Extract key points from recent conversation
    summary_points = []
    for msg in messages[-6:]:  # Last 6 messages
        if isinstance(msg, HumanMessage):
            summary_points.append(f"User asked: {msg.content[:100]}...")
        elif isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
            summary_points.append(f"Assistant responded about: {msg.content[:100]}...")
    
    return "Recent conversation context: " + " | ".join(summary_points[-4:])  # Keep last 4 points

tools = [web_search, calculator, list_directory, run_command, detect_system, get_system_info]

graph_builder = StateGraph(State)


llm = init_chat_model("google_genai:gemini-2.0-flash")
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: State):
    """Main agent node that decides whether to use tools or respond directly."""
    global conversation_summary
    
    messages = state["messages"]
    current_summary = state.get("conversation_summary", "")
    
    # Check if there's already a system message
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    
    if not has_system_message:
        system_content = """You are a helpful AI assistant with access to system tools. You MUST use tools when users request system operations:

**ALWAYS use these tools for:**
- run_command: For ANY system commands, terminal operations, navigation (cd), file operations, administrative tasks
- list_directory: To show directory contents and file listings  
- web_search: For current information, news, or facts you're unsure about
- calculator: For mathematical calculations and computations
- detect_system: To identify the operating system
- get_system_info: To get detailed system information

**Answer directly only for:** Pure conversations, explanations of concepts you already know

**Critical Guidelines:**
- When user asks to "cd" or navigate directories, ALWAYS use run_command tool
- When user asks for system commands, file operations, ALWAYS use run_command tool
- When user asks to list files or directory contents, use list_directory or run_command tool
- Never say you "cannot" do something if you have a tool that can do it
- Always try to help by using the appropriate tools"""

        if current_summary:
            system_content += f"\n\n**Previous conversation context:** {current_summary}"
        
        system_msg = SystemMessage(content=system_content)
        messages = [system_msg] + messages
    
    response = llm_with_tools.invoke(messages)
    
    # Update conversation summary if conversation is getting long
    if len(messages) > 8:
        conversation_summary = summarize_conversation(messages)
    
    return {"messages": [response], "conversation_summary": conversation_summary}

def should_continue(state: State) -> Literal["tools", "end"]:
    """Decide whether to use tools or end the conversation."""
    last_message = state["messages"][-1]
    
    # Only use tools if the AI explicitly calls them
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "end"

# Create tool node
tool_node = ToolNode(tools)

# Add nodes to graph
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

# Add edges
graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END}
)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()

def save_graph_visualization():
    """Save the graph visualization as PNG file."""
    try:
        graph_png = graph.get_graph().draw_mermaid_png()
        with open("/home/shynneri/Documents/project/ai_agent/graph_visualization.png", "wb") as f:
            f.write(graph_png)
        print("Graph visualization saved as 'graph_visualization.png'")
    except Exception as e:
        print(f"Could not save graph visualization: {e}")

def stream_graph_updates(user_input: str):
    global conversation_history, conversation_summary
    
    # Add user message to history
    user_message = HumanMessage(content=user_input)
    conversation_history.append(user_message)
    
    # Use recent messages + summary for context
    recent_messages = conversation_history[-4:]  # Keep last 4 messages for immediate context
    
    initial_state = {
        "messages": recent_messages,
        "conversation_summary": conversation_summary
    }
    
    for event in graph.stream(initial_state):
        for value in event.values():
            if "messages" in value:
                last_msg = value["messages"][-1]
                if hasattr(last_msg, 'content') and last_msg.content:
                    print("Assistant:", last_msg.content)
                    # Add assistant response to history
                    conversation_history.append(last_msg)
            
            # Update summary if provided
            if "conversation_summary" in value:
                conversation_summary = value["conversation_summary"]

if __name__ == "__main__":
    # Save graph visualization on startup
    save_graph_visualization()
    
    print("AI Assistant started. Type 'quit', 'exit', or 'q' to exit.")
    print("The assistant will remember our conversation context.\n")
    
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            stream_graph_updates(user_input)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break

