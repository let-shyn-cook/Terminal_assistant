from langchain_core.tools import tool
import os
import subprocess
import pexpect
from pathlib import Path

# Global variable to track current working directory
_current_dir = os.getcwd()

def _get_sudo_password():
    """Read sudo password from sudopass.txt file."""
    try:
        password_file = Path(__file__).parent.parent.parent / "sudopass.txt"
        with open(password_file, 'r') as f:
            return f.read().strip()
    except Exception as e:
        return None

def _ask_user_permission(command: str) -> bool:
    """Ask user for permission to run sudo command."""
    print(f"\n⚠️  SUDO COMMAND DETECTED: {command}")
    print("This command requires administrator privileges.")
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    return response in ['y', 'yes']

@tool
def detect_system() -> str:
    """Detect the operating system and distribution."""
    try:
        # Check for various OS release files
        if os.path.exists('/etc/arch-release'):
            return "Arch Linux"
        elif os.path.exists('/etc/debian_version'):
            return "Debian/Ubuntu"
        elif os.path.exists('/etc/redhat-release'):
            return "Red Hat/CentOS"
        elif os.path.exists('/etc/fedora-release'):
            return "Fedora"
        elif os.path.exists('/etc/opensuse-release'):
            return "openSUSE"
        
        # Check for package managers
        package_managers = {
            'pacman': 'Arch-based',
            'apt': 'Debian-based',
            'yum': 'Red Hat-based',
            'dnf': 'Fedora-based',
            'zypper': 'openSUSE-based'
        }
        
        for pm, distro in package_managers.items():
            try:
                subprocess.run(['which', pm], capture_output=True, check=True)
                return distro
            except subprocess.CalledProcessError:
                continue
        
        # Fallback to uname
        result = subprocess.run(['uname', '-s'], capture_output=True, text=True)
        if result.returncode == 0:
            system = result.stdout.strip()
            return system
        
        return "Unknown system"
    except Exception as e:
        return f"Detection error: {str(e)}"

@tool
def get_system_info() -> str:
    """Get comprehensive system information including OS, kernel, and available package managers."""
    try:
        info = []
        
        # Get OS info
        system = detect_system()
        info.append(f"System: {system}")
        
        # Get kernel info
        kernel_result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
        if kernel_result.returncode == 0:
            info.append(f"Kernel: {kernel_result.stdout.strip()}")
        
        # Check available package managers
        package_managers = ['pacman', 'apt', 'yum', 'dnf', 'zypper', 'brew']
        available_pm = []
        
        for pm in package_managers:
            try:
                subprocess.run(['which', pm], capture_output=True, check=True)
                available_pm.append(pm)
            except subprocess.CalledProcessError:
                continue
        
        if available_pm:
            info.append(f"Available package managers: {', '.join(available_pm)}")
        
        return '\n'.join(info)
    except Exception as e:
        return f"Error getting system info: {str(e)}"

@tool
def list_directory(path: str = ".") -> str:
    """List files and directories in the specified path. Default is current directory."""
    global _current_dir
    
    # If path is relative, make it relative to current working directory
    if not os.path.isabs(path):
        path = os.path.join(_current_dir, path)
    
    try:
        items = os.listdir(path)
        if not items:
            return f"Directory '{path}' is empty."
        
        result = f"Contents of '{path}':\n"
        for item in sorted(items):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                result += f"📁 {item}/\n"
            else:
                result += f"📄 {item}\n"
        return result
    except Exception as e:
        return f"Error listing directory '{path}': {str(e)}"

@tool
def run_command(command: str) -> str:
    """Execute any terminal command including sudo commands with automatic password handling."""
    global _current_dir
    
    if not command.strip():
        return "Error: Empty command provided"
    
    # Handle cd command specially
    if command.strip().startswith('cd'):
        parts = command.strip().split(maxsplit=1)
        if len(parts) == 1:
            # cd without arguments goes to home directory
            target_dir = os.path.expanduser('~')
        else:
            target_dir = parts[1]
            # Expand ~ and environment variables first
            target_dir = os.path.expanduser(target_dir)
            target_dir = os.path.expandvars(target_dir)
            # Handle relative paths (after expansion)
            if not os.path.isabs(target_dir):
                target_dir = os.path.join(_current_dir, target_dir)
        
        try:
            # Resolve the path and check if it exists
            target_dir = os.path.abspath(target_dir)
            if os.path.isdir(target_dir):
                _current_dir = target_dir
                return f"Changed directory to: {_current_dir}"
            else:
                return f"cd: no such file or directory: {target_dir}"
        except Exception as e:
            return f"cd: error changing directory: {str(e)}"
    
    # Check if command requires sudo
    is_sudo_command = command.strip().startswith('sudo')
    
    if is_sudo_command:
        # For web interface, we'll skip the interactive permission request
        # and just try to use the password from file
        sudo_password = _get_sudo_password()
        if not sudo_password:
            return "Error: Could not read sudo password from sudopass.txt. Sudo commands require password setup."
        
        # Use pexpect for interactive sudo commands
        try:
            timeout_duration = 120  # 2 minutes timeout
            
            child = pexpect.spawn(command, cwd=_current_dir, timeout=timeout_duration)
            
            # Wait for password prompt and send password
            try:
                index = child.expect([
                    r'\[sudo\] password for.*:',
                    r'Password:',
                    r'password:',
                    pexpect.EOF,
                    pexpect.TIMEOUT
                ], timeout=10)
                
                if index < 3:  # Password prompt detected
                    child.sendline(sudo_password)
                    
            except pexpect.TIMEOUT:
                pass  # Continue anyway
            
            # Handle confirmation prompts
            while True:
                try:
                    index = child.expect([
                        r'Proceed with installation\? \[Y/n\]',
                        r'\[Y/n\]',
                        r'\(y/N\)',
                        r'Continue\? \[Y/n\]',
                        r'Do you want to continue\? \[Y/n\]',
                        pexpect.EOF,
                        pexpect.TIMEOUT
                    ], timeout=30)
                    
                    if index < 5:  # Any confirmation prompt
                        child.sendline('y')
                    elif index == 5:  # EOF - command completed
                        break
                    else:  # TIMEOUT
                        child.expect(pexpect.EOF, timeout=timeout_duration)
                        break
                        
                except pexpect.TIMEOUT:
                    break
            
            child.close(force=False)
            output = child.before.decode('utf-8', errors='ignore')
            exit_status = child.exitstatus or 0
            
            if exit_status == 0:
                return f"Command: {command}\nWorking directory: {_current_dir}\nStatus: Success\nOutput:\n{output}"
            else:
                return f"Command: {command}\nWorking directory: {_current_dir}\nStatus: Failed (exit code {exit_status})\nOutput:\n{output}"
                
        except pexpect.TIMEOUT:
            return f"Command '{command}' timed out after {timeout_duration} seconds."
        except Exception as e:
            return f"Error executing sudo command '{command}': {str(e)}"
    
    # For non-sudo commands, use subprocess
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60,
            cwd=_current_dir
        )
        
        output = ""
        if result.stdout:
            output += f"Output:\n{result.stdout}"
        if result.stderr:
            if output:
                output += f"\nErrors:\n{result.stderr}"
            else:
                output = f"Errors:\n{result.stderr}"
        
        if not output:
            output = "Command completed successfully (no output)"
            
        return f"Command: {command}\nWorking directory: {_current_dir}\n{output}"
        
    except subprocess.TimeoutExpired:
        return f"Command '{command}' timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"

@tool
def get_current_directory() -> str:
    """Get the current working directory."""
    global _current_dir
    return f"Current working directory: {_current_dir}"

if __name__ == "__main__":
    input_command = input("Enter a command to run: ")
    print(run_command(input_command))
