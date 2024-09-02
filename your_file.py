import threading

def trim_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    trimmed_lines = [line.strip() for line in lines]
    
    with open(file_path, 'w') as file:
        file.writelines(trimmed_lines)

def trim_file_in_background(file_path):
    thread = threading.Thread(target=trim_file, args=(file_path,))
    thread.start()

# Usage
trim_file_in_background('path/to/your/file.txt')