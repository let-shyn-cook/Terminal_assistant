from flask import Flask, render_template, request, jsonify
import webview
import threading
import os
import sys
import subprocess
import json
from pathlib import Path

# Add src directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent import stream_graph_updates, conversation_history, conversation_summary
from src.tools.system_commands import run_command, list_directory, detect_system, get_system_info

app = Flask(__name__, 
            static_folder='front_end',
            static_url_path='')

class AIAgentAPI:
    def __init__(self):
        self.conversation_history = []
        self.conversation_summary = ""

@app.route('/')
def index():
    """Serve the main HTML page"""
    return app.send_static_file('index.html')

@app.route('/api/command', methods=['POST'])
def execute_command():
    """Execute system commands"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Execute the command using our system_commands tool
        result = run_command(command)
        
        return jsonify({
            'result': result,
            'command': command,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error executing command: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/ai', methods=['POST'])
def execute_ai_query():
    """Execute AI queries using the agent - backend processing only"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process the query directly in backend without streaming
        try:
            # Import the agent's internal functions for direct processing
            from src.agent import graph, conversation_history, conversation_summary
            from langchain_core.messages import HumanMessage
            
            # Add user message to history
            user_message = HumanMessage(content=query)
            conversation_history.append(user_message)
            
            # Use recent messages for context
            recent_messages = conversation_history[-4:]
            
            initial_state = {
                "messages": recent_messages,
                "conversation_summary": conversation_summary
            }
            
            # Process through the graph and collect the final response
            final_response = ""
            for event in graph.stream(initial_state):
                for value in event.values():
                    if "messages" in value:
                        last_msg = value["messages"][-1]
                        if hasattr(last_msg, 'content') and last_msg.content:
                            final_response = last_msg.content
                            # Add assistant response to history
                            conversation_history.append(last_msg)
            
            if not final_response:
                final_response = "I processed your request successfully."
                
            return jsonify({
                'result': final_response,
                'query': query,
                'status': 'success'
            })
            
        except Exception as agent_error:
            return jsonify({
                'error': f'AI Agent Error: {str(agent_error)}',
                'status': 'error'
            }), 500
        
    except Exception as e:
        return jsonify({
            'error': f'Error processing AI query: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/system-info', methods=['GET'])
def get_system_information():
    """Get system information"""
    try:
        system_info = get_system_info()
        return jsonify({
            'result': system_info,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': f'Error getting system info: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/list-directory', methods=['POST'])
def list_dir():
    """List directory contents"""
    try:
        data = request.get_json()
        path = data.get('path', '.')
        
        result = list_directory(path)
        
        return jsonify({
            'result': result,
            'path': path,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error listing directory: {str(e)}',
            'status': 'error'
        }), 500

def start_flask_server():
    """Start the Flask server in a separate thread"""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def create_webview_window():
    """Create and configure the webview window"""
    webview.create_window(
        title='AI Agent Terminal',
        url='http://127.0.0.1:5000',
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False,
        minimized=False,
        on_top=False,
        shadow=True,
    )

def main():
    """Main application entry point"""
    print("🤖 Starting AI Agent Terminal...")
    print("📁 Frontend: front_end/")
    print("🔧 Backend: app.py")
    print("⚡ Agent: src/agent.py")
    print("🛠️  System Commands: src/tools/system_commands.py")
    print("-" * 50)
    
    # Check if --no-webview flag is passed
    import sys
    if '--no-webview' in sys.argv:
        print("🌐 Starting Flask server only (no webview)")
        print("🔗 Open http://127.0.0.1:5000 in your browser")
        app.run(host='127.0.0.1', port=5000, debug=False)
        return
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    
    # Wait a moment for the server to start
    import time
    time.sleep(2)
    
    print("🌐 Flask server started on http://127.0.0.1:5000")
    print("🚀 Opening webview window...")
    
    # Create and start the webview with Qt GUI explicitly
    create_webview_window()
    webview.start(gui='qt', debug=False)

if __name__ == '__main__':
    main()