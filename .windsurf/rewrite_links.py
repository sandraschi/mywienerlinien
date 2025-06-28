import os
import re
import logging
import sys

# --- Logger Setup (using the proven basicConfig pattern) ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'rewrite_links.log')

try:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
except Exception as e:
    # Fallback for catastrophic logging failure
    print(f"CRITICAL: Failed to configure logger. Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- Main Script ---
DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def rewrite_file_with_fixed_links(original_file_path):
    relative_file_path = os.path.relpath(original_file_path, DOCS_ROOT)
    logging.debug(f"--- Processing: {relative_file_path}")

    try:
        with open(original_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Could not read file {relative_file_path}. Skipping. Error: {e}")
        return

    file_dir = os.path.dirname(original_file_path)
    changes_made = 0

    # Use a function for replacement to handle scope and logic cleanly
    def replacement_logic(match):
        nonlocal changes_made
        link_text = match.group(1)
        link_target = match.group(2).strip()

        # Ignore external, anchor, or non-markdown links
        if link_target.startswith(('http', '#', 'mailto:')) or not link_target or not link_target.endswith('.md'):
            return match.group(0) # Return the original link

        root_relative_path_check = os.path.normpath(os.path.join(DOCS_ROOT, link_target))
        is_valid_as_root_relative = os.path.exists(root_relative_path_check)

        file_relative_path_check = os.path.normpath(os.path.join(file_dir, link_target))
        is_valid_as_file_relative = os.path.exists(file_relative_path_check)

        if is_valid_as_root_relative:
            return match.group(0) # Link is already correct
        elif is_valid_as_file_relative:
            correct_path = os.path.relpath(file_relative_path_check, DOCS_ROOT).replace('\\', '/')
            new_link = f'[{link_text}]({correct_path})'
            logging.warning(f"Fixing link in '{relative_file_path}': '{link_target}' -> '{correct_path}'")
            changes_made += 1
            return new_link
        else:
            logging.error(f"BROKEN link in '{relative_file_path}': '{link_target}'. Target not found. Leaving as is.")
            return match.group(0) # Return the original broken link

    # Perform the replacement
    try:
        new_content = LINK_REGEX.sub(replacement_logic, content)
    except Exception as e:
        logging.error(f"Failed during regex substitution on {relative_file_path}. Skipping. Error: {e}")
        return

    # Write to a new file if changes were made
    if changes_made > 0:
        new_file_path = original_file_path.replace('.md', '_fixed.md')
        logging.info(f"Found {changes_made} fix(es) for {relative_file_path}. Writing to {os.path.basename(new_file_path)}.")
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            logging.error(f"Failed to write new file {os.path.basename(new_file_path)}. Error: {e}")
    else:
        logging.debug(f"No changes needed for {relative_file_path}.")

def main():
    logging.info("--- Starting Link Rewriter --- safe mode, creates _fixed.md files ---")
    logging.info(f'Analyzing documentation in: {DOCS_ROOT}')
    
    try:
        for root, _, files in os.walk(DOCS_ROOT):
            for file in files:
                if file.endswith('.md') and not file.endswith('_fixed.md'):
                    rewrite_file_with_fixed_links(os.path.join(root, file))
    except Exception as e:
        logging.critical(f"A critical error occurred during the file walk. Aborting. Error: {e}")

    logging.info('--- Script Finished ---')

if __name__ == '__main__':
    main()
