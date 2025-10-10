import sys
import os
import socket
import shlex
import argparse
import csv
import base64

class VFSNode:
    def __init__(self, name, node_type, content=None):
        self.name = name
        self.type = node_type  # 'file' или 'dir'
        self.content = content
        self.children = {}

class VFS:
    def __init__(self):
        self.root = VFSNode("", "dir")
        self.current_path = "/"

    def load_from_csv(self, csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    path = row['path']
                    node_type = row['type']
                    content = row.get('content', '')
                    
                    if node_type == 'file' and content:
                        try:
                            content = base64.b64decode(content).decode('utf-8')
                        except Exception as e:
                            content = f"Error decoding content: {e}"
                    
                    self._add_node(path, node_type, content)
        except FileNotFoundError:
            raise Exception(f"VFS file not found: {csv_path}")
        except Exception as e:
            raise Exception(f"Error loading VFS: {e}")

    def _add_node(self, path, node_type, content):
        if path == "/":
            return
        
        parts = [p for p in path.split('/') if p]
        current = self.root
        
        for part in parts[:-1]:
            if part not in current.children:
                current.children[part] = VFSNode(part, "dir")
            current = current.children[part]
        
        name = parts[-1]
        current.children[name] = VFSNode(name, node_type, content)

    def get_current_dir(self):
        parts = [p for p in self.current_path.split('/') if p]
        current = self.root
        for part in parts:
            if part in current.children:
                current = current.children[part]
            else:
                return None
        return current

def get_prompt(custom_prompt=None, vfs=None):
    if custom_prompt:
        return custom_prompt
    username = os.getlogin()
    hostname = socket.gethostname()
    current_dir = vfs.current_path if vfs else "~"
    return f"{username}@{hostname}:{current_dir}$ "

def handle_command(command_line, vfs):
    try:
        parts = shlex.split(command_line)
        if not parts:
            return ""
        
        cmd = parts[0]
        args = parts[1:]
        
        if cmd == "exit":
            print("Exiting emulator.")
            sys.exit(0)
        elif cmd == "ls":
            return handle_ls(args, vfs)
        elif cmd == "cd":
            return handle_cd(args, vfs)
        else:
            return f"Command not found: {cmd}"
    except ValueError as e:
        return f"Parsing error: {e}"

def handle_ls(args, vfs):
    if not vfs:
        return "VFS not loaded"
    
    current_dir = vfs.get_current_dir()
    if not current_dir:
        return "Invalid directory"
    
    if current_dir.type != "dir":
        return "Not a directory"
    
    items = list(current_dir.children.keys())
    return " ".join(items) if items else ""

def handle_cd(args, vfs):
    if not vfs:
        return "VFS not loaded"
    
    if len(args) != 1:
        return "cd: missing argument"
    
    target_path = args[0]
    
    # Абсолютный или относительный путь
    if target_path.startswith("/"):
        new_path = target_path
    else:
        current = vfs.current_path
        if current == "/":
            new_path = f"/{target_path}"
        else:
            new_path = f"{current}/{target_path}"
    
    # Нормализация пути
    parts = [p for p in new_path.split('/') if p and p != '.']
    resolved_parts = []
    for part in parts:
        if part == "..":
            if resolved_parts:
                resolved_parts.pop()
        else:
            resolved_parts.append(part)
    
    new_path = "/" + "/".join(resolved_parts)
    
    # Проверка существования пути
    test_parts = [p for p in new_path.split('/') if p]
    current = vfs.root
    for part in test_parts:
        if part in current.children and current.children[part].type == "dir":
            current = current.children[part]
        else:
            return f"cd: {target_path}: No such directory"
    
    vfs.current_path = new_path
    return ""

def execute_script(script_path, vfs):
    try:
        with open(script_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # Поддержка комментариев
                    print(f"{get_prompt(vfs=vfs)} {line}")
                    output = handle_command(line, vfs)
                    if output:
                        print(output)
    except FileNotFoundError:
        print(f"Error: Script file {script_path} not found.")
    except Exception as e:
        print(f"Error executing script: {e}")

def main():
    parser = argparse.ArgumentParser(description="Shell Emulator (Variant 6)")
    parser.add_argument("--vfs-path", help="Path to VFS CSV file")
    parser.add_argument("--prompt", help="Custom prompt string")
    parser.add_argument("--script", help="Path to startup script")
    args = parser.parse_args()

    print("Debug: Starting emulator with parameters:")
    print(f"  VFS Path: {args.vfs_path or 'Not specified'}")
    print(f"  Custom Prompt: {args.prompt or 'Not specified'}")
    print(f"  Script Path: {args.script or 'Not specified'}")

    vfs = None
    if args.vfs_path:
        try:
            vfs = VFS()
            vfs.load_from_csv(args.vfs_path)
            print("VFS loaded successfully")
        except Exception as e:
            print(f"Error loading VFS: {e}")
            vfs = None

    if args.script:
        execute_script(args.script, vfs)
    else:
        print("Shell Emulator (Variant 6, Stage 3 - VFS)")
        while True:
            prompt = get_prompt(args.prompt, vfs)
            command_line = input(prompt).strip()
            output = handle_command(command_line, vfs)
            if output:
                print(output)

if __name__ == "__main__":
    main()
