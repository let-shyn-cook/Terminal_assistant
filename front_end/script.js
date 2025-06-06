class TerminalApp {
    constructor() {
        this.commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
        this.historyIndex = -1;
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadHistory();
    }

    initializeElements() {
        this.terminal = document.getElementById('terminal');
        this.output = document.getElementById('output');
        this.input = document.getElementById('commandInput');
        this.status = document.getElementById('status');
        this.clearBtn = document.getElementById('clearBtn');
        this.historyBtn = document.getElementById('historyBtn');
    }

    bindEvents() {
        // Enter key to execute command
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !this.isProcessing) {
                this.executeCommand();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateHistory('up');
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateHistory('down');
            }
        });

        // Clear button
        this.clearBtn.addEventListener('click', () => this.clearTerminal());

        // History button
        this.historyBtn.addEventListener('click', () => this.showHistory());

        // Auto-focus input
        document.addEventListener('click', () => {
            if (!window.getSelection().toString()) {
                this.input.focus();
            }
        });
    }

    async executeCommand() {
        const command = this.input.value.trim();
        if (!command) return;

        // Add to history
        this.addToHistory(command);
        
        // Display command
        this.addCommandToOutput(command);
        
        // Clear input and set processing state
        this.input.value = '';
        this.setProcessing(true);

        try {
            let result;
            if (command.toLowerCase() === 'clear') {
                this.clearTerminal();
                this.setProcessing(false);
                return;
            }

            // Check if it's a gem (AI) command
            if (command.toLowerCase().startsWith('gem ')) {
                const query = command.substring(4).trim();
                result = await this.executeAICommand(query);
                this.addOutputToTerminal(result, 'ai-response');
            } else {
                // Execute system command
                result = await this.executeSystemCommand(command);
                this.addOutputToTerminal(result, result.includes('Error') ? 'error' : 'success');
            }
        } catch (error) {
            this.addOutputToTerminal(`Error: ${error.message}`, 'error');
        } finally {
            this.setProcessing(false);
        }
    }

    async executeSystemCommand(command) {
        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command })
            });

            const data = await response.json();
            return data.result || data.error || 'Command executed';
        } catch (error) {
            return `Network error: ${error.message}`;
        }
    }

    async executeAICommand(query) {
        try {
            const response = await fetch('/api/ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            return data.result || data.error || 'AI query processed';
        } catch (error) {
            return `AI service error: ${error.message}`;
        }
    }

    addCommandToOutput(command) {
        const commandDiv = document.createElement('div');
        commandDiv.className = 'command-line';
        
        const commandSpan = document.createElement('div');
        commandSpan.className = 'command';
        
        // Syntax highlighting
        const highlightedCommand = this.highlightSyntax(command);
        commandSpan.innerHTML = `<span class="prompt">$ </span>${highlightedCommand}`;
        
        commandDiv.appendChild(commandSpan);
        this.output.appendChild(commandDiv);
        this.scrollToBottom();
    }

    addOutputToTerminal(text, type = '') {
        const outputDiv = document.createElement('div');
        outputDiv.className = `output ${type}`;
        outputDiv.textContent = text;
        
        this.output.appendChild(outputDiv);
        this.scrollToBottom();
    }

    highlightSyntax(command) {
        // Basic syntax highlighting
        let highlighted = command;
        
        if (command.toLowerCase().startsWith('gem ')) {
            highlighted = `<span class="syntax-highlight gem">gem</span> ${command.substring(4)}`;
        } else {
            // Highlight common commands
            const commonCommands = ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep', 'find', 'sudo'];
            const words = command.split(' ');
            
            if (commonCommands.includes(words[0])) {
                words[0] = `<span class="syntax-highlight command">${words[0]}</span>`;
            }
            
            // Highlight flags
            for (let i = 1; i < words.length; i++) {
                if (words[i].startsWith('-')) {
                    words[i] = `<span class="syntax-highlight flag">${words[i]}</span>`;
                } else if (words[i].includes('/')) {
                    words[i] = `<span class="syntax-highlight path">${words[i]}</span>`;
                }
            }
            
            highlighted = words.join(' ');
        }
        
        return highlighted;
    }

    addToHistory(command) {
        if (command && this.commandHistory[this.commandHistory.length - 1] !== command) {
            this.commandHistory.push(command);
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
            localStorage.setItem('commandHistory', JSON.stringify(this.commandHistory));
        }
        this.historyIndex = -1;
    }

    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;

        if (direction === 'up') {
            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }
        } else if (direction === 'down') {
            if (this.historyIndex === -1) return;
            if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
            } else {
                this.historyIndex = -1;
                this.input.value = '';
                return;
            }
        }

        this.input.value = this.commandHistory[this.historyIndex] || '';
    }

    showHistory() {
        if (this.commandHistory.length === 0) {
            this.addOutputToTerminal('No command history available', '');
            return;
        }

        const historyText = 'Command History:\n' + 
            this.commandHistory
                .slice(-10)
                .map((cmd, idx) => `${idx + 1}. ${cmd}`)
                .join('\n');
        
        this.addOutputToTerminal(historyText, '');
    }

    loadHistory() {
        // Display welcome message with some recent history if available
        if (this.commandHistory.length > 0) {
            const recentCommands = this.commandHistory.slice(-3);
            const historyMsg = `\nRecent commands: ${recentCommands.join(', ')}`;
            const welcomeDiv = this.output.querySelector('.welcome');
            if (welcomeDiv) {
                welcomeDiv.innerHTML += historyMsg;
            }
        }
    }

    clearTerminal() {
        this.output.innerHTML = `
            <div class="welcome">
                Welcome to AI Agent Terminal!<br>
                • Type any system command to execute it<br>
                • Start with "gem" followed by natural language for AI assistance<br>
                • Type "clear" to clear the terminal<br>
            </div>
        `;
        this.scrollToBottom();
    }

    setProcessing(processing) {
        this.isProcessing = processing;
        if (processing) {
            this.status.textContent = 'Processing';
            this.status.className = 'status loading';
            this.input.disabled = true;
            this.addOutputToTerminal('Processing...', 'loading-dots');
        } else {
            this.status.textContent = 'Ready';
            this.status.className = 'status';
            this.input.disabled = false;
            this.input.focus();
            
            // Remove processing message
            const loadingDots = this.output.querySelector('.loading-dots');
            if (loadingDots) {
                loadingDots.remove();
            }
        }
    }

    scrollToBottom() {
        this.output.scrollTop = this.output.scrollHeight;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TerminalApp();
});

// Add some utility functions for enhanced functionality
window.addEventListener('beforeunload', (e) => {
    // Save any pending state
    const app = window.terminalApp;
    if (app && app.isProcessing) {
        e.preventDefault();
        e.returnValue = 'Command is still processing. Are you sure you want to leave?';
    }
});
