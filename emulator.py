import sys
import os
import socket
import shlex
import argparse
import csv
import base64
from io import StringIO

class VFSNode:
    def __init__(self, node_type, content=None):
        self.type = node_type
        self.content = content  # bytes for files, None for dirs
        self.children = {} if node_type == 'dir' else None

def load_vfs(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"VFS file not found: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse CSV
    csv_reader = csv.DictReader(StringIO(content))
    if not all(col in csv_reader.fieldnames for col in ['path', 'type', 'content']):
        raise ValueError("Invalid VFS format: missing required columns (path, type, content)")
    
    vfs_root = VFSNode('dir')
    paths = {}
    
    for row in csv_reader:
        path = row['path'].strip()
        node_type = row['type'].strip()
        content_str = row['content'].strip()
        
        if node_type not in ['dir', 'file']:
            raise ValueError(f"Invalid type '{node_type}' in path {path}")
        
        if path == '/':
            if node_type != 'dir':
                raise ValueError("Root must be a directory")
            continue  # Root already created
        
        if not path.startswith('/'):
            raise ValueError(f"Path must be absolute: {path}")
        
        parts = path.strip('/').split('/')
        current = vfs_root
        current_path = ''
        
        for i, part in enumerate(parts):
            if not part:
                continue
            current_path = f"{current_path}/{part}"
            
            if part not in current.children:
                if i == len(parts) - 1:
                    # Create this node
                    if node_type == 'file':
                        try:
                            content_bytes = base64.b64decode(content_str)
                        except:
                            raise ValueError(f"Invalid base64 content for {path}")
                        current.children[part] = VFSNode('file', content_bytes)
                    else:
                        current.children[part] = VFSNode('dir')
                else:
                    # Parent dir missing
                    raise ValueError(f"Missing parent directory for {path}")
            else:
                # Existing, check type
                if i == len(parts) - 1 and current.children[part].type != node_type:
                    raise ValueError(f"Type mismatch for {path}")
            
            if current.children[part].type != 'dir' and i < len(parts) - 1:
                raise ValueError(f"Non-dir in path: {current_path}")
            
            current = current.children[part]
    
    return vfs_root

def get_prompt(current_dir='/'):
    username = os.getlogin()
    hostname = socket.gethostname()
    return f"{username}@{hostname}:{current_dir}$ "

def handle_command(command_line, vfs_root, current_dir):
    try:
        parts = shlex.split(command_line)
        if not parts:
            return ""
        
        cmd = parts[0]
        args = parts[1:]
        
        if cmd == "exit":
            print("Exiting emulator.")
            sys.exit(0)
        elif cmd in ["ls", "cd"]:
            return f"{cmd} {' '.join(args)}"  # Заглушка
        else:
            return f"Command not found: {cmd}"
    except ValueError as e:
        return f"Parsing error: {e}"

def execute_script(script_path, vfs_root, current_dir):
    try:
        with open(script_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):  # Игнор пустых и комментариев
                    continue
                print(f"{get_prompt(current_dir)} {line}")
                output = handle_command(line, vfs_root, current_dir)
                if output:
                    print(output)
                if "error" in output.lower() or "not found" in output.lower():
                    print(f"Script execution stopped due to error in: {line}")
                    break
    except FileNotFoundError:
        print(f"Error: Script file {script_path} not found.")
    except Exception as e:
        print(f"Error executing script: {e}")

def main():
    parser = argparse.ArgumentParser(description="Shell Emulator (Variant 6)")
    parser.add_argument("--vfs-path", help="Path to VFS CSV file")
    parser.add_argument("--script", help="Path to startup script")
    args = parser.parse_args()

    # Отладочный вывод
    print("Debug: Starting emulator with parameters:")
    print(f"  VFS Path: {args.vfs_path or 'Not specified'}")
    print(f"  Script Path: {args.script or 'Not specified'}")

    vfs_root = None
    current_dir = '/'
    if args.vfs_path:
        try:
            vfs_root = load_vfs(args.vfs_path)
            print("VFS loaded successfully.")
        except Exception as e:
            print(f"Error loading VFS: {e}")
            sys.exit(1)

    if args.script:
        execute_script(args.script, vfs_root, current_dir)
    else:
        print("Shell Emulator (Variant 6, Stage 3)")
        while True:
            prompt = get_prompt(current_dir)
            command_line = input(prompt).strip()
            output = handle_command(command_line, vfs_root, current_dir)
            if output:
                print(output)

if __name__ == "__main__":
    main()
