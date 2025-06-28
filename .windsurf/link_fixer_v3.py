import os
import re
import logging
from logging.handlers import RotatingFileHandler

# --- Configuration ---
# Set to False to apply changes. Set to True to only log what would be changed.
DRY_RUN = True

# --- Logger Setup ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'link_fixer_v3.log')

# Create logger
logger = logging.getLogger('LinkFixerV3')
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if logger.handlers:
    logger.handlers = []

# Console handler (shows INFO and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler (shows DEBUG and above)
file_handler = RotatingFileHandler(log_file, mode='w', maxBytes=5*1024*1024, backupCount=2)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- Main Script ---
DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
# CORRECTED Regex: This was the source of all previous failures.
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def fix_links_in_file(file_path):
    relative_file_path = os.path.relpath(file_path, DOCS_ROOT)
    logger.debug(f"--- Processing: {relative_file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Could not read file {relative_file_path}. Error: {e}")
        return

    original_content = content
    file_dir = os.path.dirname(file_path)
    replacements = []

    for match in LINK_REGEX.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2).strip()

        # --- Filtering ---
        if link_target.startswith(('http', '#', 'mailto:')) or not link_target or not link_target.endswith('.md'):
            logger.debug(f"Ignoring non-fixable link: '{link_target}'")
            continue

        # --- Path Analysis ---
        root_relative_path_check = os.path.normpath(os.path.join(DOCS_ROOT, link_target))
        is_valid_as_root_relative = os.path.exists(root_relative_path_check)

        file_relative_path_check = os.path.normpath(os.path.join(file_dir, link_target))
        is_valid_as_file_relative = os.path.exists(file_relative_path_check)

        # --- Decision Logic ---
        if is_valid_as_root_relative:
            logger.debug(f"Link '{link_target}' is already correct.")
        elif is_valid_as_file_relative:
            correct_path = os.path.relpath(file_relative_path_check, DOCS_ROOT).replace('\\', '/')
            logger.warning(f"File '{relative_file_path}': Link '[{link_text}]({link_target})' needs to be changed to '{correct_path}'.")
            replacements.append((match.group(0), f'[{link_text}]({correct_path})'))
        else:
            logger.error(f"File '{relative_file_path}': Link '[{link_text}]({link_target})' is BROKEN. Target not found.")

    # --- Apply Changes if not in DRY_RUN ---
    if replacements and not DRY_RUN:
        logger.info(f"Applying {len(replacements)} fix(es) to {relative_file_path}.")
        for old, new in replacements:
            content = content.replace(old, new)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to write changes to {relative_file_path}. Error: {e}")
    elif replacements and DRY_RUN:
        logger.info(f"Found {len(replacements)} link(s) that need fixing in {relative_file_path}. (DRY RUN)")
    else:
        logger.debug(f"No changes needed for {relative_file_path}.")


def main():
    if DRY_RUN:
        logger.info("--- Starting Link Fixer v3 in DRY RUN mode. No files will be changed. ---")
    else:
        logger.info("--- Starting Link Fixer v3 in APPLY mode. Files will be changed. ---")

    logger.info(f'Analyzing documentation in: {DOCS_ROOT}')
    for root, _, files in os.walk(DOCS_ROOT):
        for file in files:
            if file.endswith('.md'):
                fix_links_in_file(os.path.join(root, file))
    logger.info('--- Script Finished ---')

if __name__ == '__main__':
    main()
