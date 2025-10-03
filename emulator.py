import sys
import os
import socket
import shlex
import argparse

class VFS:
    def __init__(self):
        self.root = {}
        self.current_dir = self.root

    def load_from_dir(self, path):
        self.root = {}
        self.current_dir = self.root
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                self.root[item] = {"type": "file", "content": None}
            else:  # Директория
                self.root[item] = {"type": "dir", "content": {}}
                # Рекурсивно загружаем содержимое вложенной директории
                self._load_recursive(full_path, self.root[item]["content"])
        print(f"VFS loaded from {path}")

    def _load_recursive(self, path, target_dict):
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                target_dict[item] = {"type": "file", "content": None}
            else:
                target_dict[item] = {"type": "dir", "content": {}}
                self._load_recursive(full_path, target_dict[item]["content"])

    def ls(self, args):
        if not args:
            return "\n".join(self.current_dir.keys())
        return f"ls: too many arguments"

    def cd(self, args):
        if not args:
            return "cd: missing argument"
        dir_name = args[0]
        if dir_name in self.current_dir and self.current_dir[dir_name]["type"] == "dir":
            self.current_dir = self.current_dir[dir_name]["content"]
            return ""
        return f"cd: {dir_name}: No such directory"

    def mkdir(self, args):
        if not args:
            return "mkdir: missing argument"
        dir_name = args[0]
        if dir_name not in self.current_dir:
            self.current_dir[dir_name] = {"type": "dir", "content": {}}
            return ""
        return f"mkdir: {dir_name}: Directory already exists"

def get_prompt(custom_prompt=None, vfs=None):
    if custom_prompt:
        return custom_prompt
    username = os.getlogin()
    hostname = socket.gethostname()
    current_dir = "~"  # Пока фиксированное значение
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
            return vfs.ls(args)
        elif cmd == "cd":
            return vfs.cd(args)
        elif cmd == "mkdir":
            return vfs.mkdir(args)
        elif cmd == "vfs-load":
            if args:
                vfs.load_from_dir(args[0])
                return ""
            return "vfs-load: missing path argument"
        else:
            return f"Command not found: {cmd}"
    except ValueError as e:
        return f"Parsing error: {e}"

def execute_script(script_path, vfs):
    try:
        with open(script_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    print(f"{get_prompt(None, vfs)} {line}")
                    output = handle_command(line, vfs)
                    if output:
                        print(output)
                    if "error" in output.lower():
                        print(f"Script execution stopped due to error in: {line}")
                        break
    except FileNotFoundError:
        print(f"Error: Script file {script_path} not found.")
    except Exception as e:
        print(f"Error executing script: {e}")

def main():
    vfs = VFS()
    parser = argparse.ArgumentParser(description="Shell Emulator (Variant 6)")
    parser.add_argument("--vfs-path", help="Path to VFS directory")
    parser.add_argument("--prompt", help="Custom prompt string")
    parser.add_argument("--script", help="Path to startup script")
    args = parser.parse_args()

    print("Debug: Starting emulator with parameters:")
    print(f"  VFS Path: {args.vfs_path or 'Not specified'}")
    print(f"  Custom Prompt: {args.prompt or 'Not specified'}")
    print(f"  Script Path: {args.script or 'Not specified'}")

    if args.vfs_path:
        vfs.load_from_dir(args.vfs_path)

    if args.script:
        execute_script(args.script, vfs)
    else:
        print("Shell Emulator (Variant 6, Stage 3)")
        while True:
            prompt = get_prompt(args.prompt, vfs)
            command_line = input(prompt).strip()
            output = handle_command(command_line, vfs)
            if output:
                print(output)

if __name__ == "__main__":
    main()
