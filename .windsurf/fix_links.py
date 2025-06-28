import os
import re
import sys

def print_flush(*args, **kwargs):
    """A print function that flushes the output buffer."""
    print(*args, **kwargs, flush=True)

print_flush("--- Python script starting execution ---")

DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
# A standard regex for markdown links to .md files, excluding http/https links.
LINK_REGEX = re.compile(r'\[([^\]]+)\]\((?!https?:)([^)]+\.md))\)')

def fix_markdown_links(file_path):
    """Reads a markdown file, fixes relative links, and overwrites it if changes were made."""
    print_flush(f"\n--- Processing file: {os.path.relpath(file_path, DOCS_ROOT)}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_flush(f"    ERROR: Could not read file. {e}")
        return

    original_content = content
    file_dir = os.path.dirname(file_path)
    replacements = []

    for match in LINK_REGEX.finditer(content):
        full_match_text = match.group(0)
        link_text = match.group(1)
        relative_path = match.group(2)

        if relative_path.startswith('/'):
            print_flush(f"    Skipping root link: {relative_path}")
            continue

        print_flush(f"    Found potential relative link: {full_match_text}")
        target_abs_path = os.path.normpath(os.path.join(file_dir, relative_path))

        if not os.path.exists(target_abs_path):
            print_flush(f"    WARNING: Broken link target '{relative_path}' does not exist at '{target_abs_path}'")
            continue

        new_relative_path = os.path.relpath(target_abs_path, DOCS_ROOT).replace('\\', '/')

        if new_relative_path != relative_path:
            print_flush(f"    CHANGE DETECTED: '{relative_path}' -> '{new_relative_path}'")
            new_link = f'[{link_text}]({new_relative_path})'
            replacements.append((full_match_text, new_link))
        else:
            print_flush(f"    Link is already correct: {relative_path}")

    if replacements:
        print_flush(f"    Applying {len(replacements)} changes.")
        for old, new in replacements:
            content = content.replace(old, new)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print_flush(f"    SUCCESS: File updated.")
        except Exception as e:
            print_flush(f"    ERROR: Could not write to file. {e}")
    else:
        print_flush(f"    No changes needed.")

def main():
    """Main function to walk through the docs directory and fix links."""
    print_flush(f'--- SCRIPT MAIN ---')
    print_flush(f'Starting link fixing process in: {DOCS_ROOT}')
    
    found_files = False
    for root, _, files in os.walk(DOCS_ROOT):
        for file in files:
            if file.endswith('.md') and file != '_sidebar.md':
                found_files = True
                fix_markdown_links(os.path.join(root, file))
    
    if not found_files:
        print_flush("WARNING: No markdown files were found to process.")
        
    print_flush('\n--- SCRIPT COMPLETE ---')

if __name__ == '__main__':
    main()
