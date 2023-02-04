import sys
import os
import re

def extract_markdown_body(file_path):
    with open(file_path, 'r', encoding = 'utf-8') as file:
        lines = file.readlines()

    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            start = i + 1
            break

    end = len(lines) - 1
    for i, line in reversed(list(enumerate(lines))):
        if line.strip() == '---':
            end = i - 1
            break
    print(start, end)
    return ''.join(lines[end + 2:])

def fix_filename(file_name):
    invalid_chars = '\/:*?"<>|'
    for c in invalid_chars:
        file_name = file_name.replace(c,'')
    return file_name

def check_folder():
    # Checks if specified folder is writable
    # if len(sys.argv) > 1 and os.access(sys.argv[0], os.W_OK):
    #     return sys.argv[0]
    # else:
    #     raise Exception(
    #         'Error: Please specify output folder as the first parameter. Example:'
    #         '%(prog)s <path>')
    return os.getcwd()


def get_md_files(folder_path):
    md_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def main(folder: str):
    print(f'Looking into "{folder}"')
    files = get_md_files(folder)
    print(files)
    for filename in files:
        src_file = os.path.join(folder, filename)
        print(extract_markdown_body(src_file))
        a = input('confirm')

# Driver Code
if __name__ == '__main__':
    folder = r'F:\Obsidian-tg-channels\natural_language_processing\posts'
    # Calling main() function
    main(folder)
