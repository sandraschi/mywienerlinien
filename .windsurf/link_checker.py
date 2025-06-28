import os
import re
import sys

def print_flush(*args, **kwargs):
    """A print function that flushes the output buffer to ensure immediate output."""
    print(*args, **kwargs, flush=True)

print_flush("--- Link Checker (Diagnostic Mode) ---")

DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
# Regex to find markdown links, excluding external http/https and anchor # links.
LINK_REGEX = re.compile(r'\[([^\]]*)\]\((?!https?://|#)([^)]+))\)')

def check_links(file_path):
    """Analyzes a single markdown file and reports the status of its internal links."""
    print_flush(f"\n--- Checking: {os.path.relpath(file_path, DOCS_ROOT)}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_flush(f"    ERROR: Could not read file. {e}")
        return

    file_dir = os.path.dirname(file_path)
    found_issues = False

    for match in LINK_REGEX.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2).strip()

        if not link_target.endswith('.md'):
            continue # Ignore links to non-markdown files for this check

        # Check if the link target resolves correctly from the DOCS_ROOT
        root_relative_path = os.path.normpath(os.path.join(DOCS_ROOT, link_target))
        is_valid_root_relative = os.path.exists(root_relative_path)

        # Check if the link target resolves correctly from the file's own directory
        file_relative_path = os.path.normpath(os.path.join(file_dir, link_target))
        is_valid_file_relative = os.path.exists(file_relative_path)

        if is_valid_root_relative:
            # This is the desired format. The link is correct.
            pass
        elif is_valid_file_relative:
            # This link works but is not in the root-relative format.
            correct_path = os.path.relpath(file_relative_path, DOCS_ROOT).replace('\\', '/')
            print_flush(f"  [NEEDS FIX]: '{link_target}' should be '{correct_path}'")
            found_issues = True
        else:
            # The link is broken. It doesn't resolve either way.
            print_flush(f"  [BROKEN]: '{link_target}' in link '[{link_text}]' is invalid.")
            found_issues = True

    if not found_issues:
        print_flush("    No issues found.")

def main():
    """Main function to walk through the docs directory and check all markdown files."""
    print_flush(f'Starting link analysis in: {DOCS_ROOT}')
    for root, _, files in os.walk(DOCS_ROOT):
        for file in files:
            if file.endswith('.md'):
                check_links(os.path.join(root, file))
    print_flush('\n--- Analysis Complete ---')

if __name__ == '__main__':
    main()
