import os
import re
import logging
import sys

# --- Configuration ---
# Set to False to apply changes. Set to True to only log what would be changed.
DRY_RUN = True

# --- Logger Setup (using the proven basicConfig pattern) ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'link_fixer_final_v2.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'), # Overwrite for a clean run
        logging.StreamHandler(sys.stdout) # Explicitly write to stdout
    ]
)

# --- Main Script ---
DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def fix_links_in_file(file_path):
    relative_file_path = os.path.relpath(file_path, DOCS_ROOT)
    logging.debug(f"--- Processing: {relative_file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Could not read file {relative_file_path}. Error: {e}")
        return

    file_dir = os.path.dirname(file_path)
    replacements = []

    for match in LINK_REGEX.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2).strip()

        if link_target.startswith(('http', '#', 'mailto:')) or not link_target or not link_target.endswith('.md'):
            continue

        root_relative_path_check = os.path.normpath(os.path.join(DOCS_ROOT, link_target))
        is_valid_as_root_relative = os.path.exists(root_relative_path_check)

        file_relative_path_check = os.path.normpath(os.path.join(file_dir, link_target))
        is_valid_as_file_relative = os.path.exists(file_relative_path_check)

        if is_valid_as_root_relative:
            logging.debug(f"Link '{link_target}' is already correct.")
        elif is_valid_as_file_relative:
            correct_path = os.path.relpath(file_relative_path_check, DOCS_ROOT).replace('\\', '/')
            logging.warning(f"File '{relative_file_path}': Link '[{link_text}]({link_target})' needs to be changed to '{correct_path}'.")
            replacements.append((match.group(0), f'[{link_text}]({correct_path})'))
        else:
            logging.error(f"File '{relative_file_path}': Link '[{link_text}]({link_target})' is BROKEN. Target not found.")

    if replacements and not DRY_RUN:
        logging.info(f"Applying {len(replacements)} fix(es) to {relative_file_path}.")
        for old, new in replacements:
            content = content.replace(old, new)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Failed to write changes to {relative_file_path}. Error: {e}")
    elif replacements and DRY_RUN:
        logging.info(f"Found {len(replacements)} link(s) that need fixing in {relative_file_path}. (DRY RUN)")
    else:
        logging.debug(f"No changes needed for {relative_file_path}.")

def main():
    if DRY_RUN:
        logging.info("--- Starting Link Fixer (basicConfig) in DRY RUN mode. ---")
    else:
        logging.info("--- Starting Link Fixer (basicConfig) in APPLY mode. ---")

    logging.info(f'Analyzing documentation in: {DOCS_ROOT}')
    for root, _, files in os.walk(DOCS_ROOT):
        for file in files:
            if file.endswith('.md'):
                fix_links_in_file(os.path.join(root, file))
    logging.info('--- Script Finished ---')

if __name__ == '__main__':
    main()
