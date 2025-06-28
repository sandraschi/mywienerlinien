import os
import re
import logging
from logging.handlers import RotatingFileHandler

# --- Logger Setup (as per Rulebook) ---
LOG_DIR = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'link_checker.log')

# Create logger
logger = logging.getLogger('LinkChecker')
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers if script is run multiple times
if logger.handlers:
    logger.handlers = []

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- Main Script ---
DOCS_ROOT = os.path.abspath('d:/Dev/repos/mywienerlinien/.windsurf/docs')
# Corrected Regex:
# - Excludes http/https links
# - Excludes anchor # links
# - Captures the link text and the target path
LINK_REGEX = re.compile(r'\[([^\]]*)\]\(((?!https?://|#)[^)]+))\)')

def check_links_in_file(file_path):
    """Analyzes a single markdown file and reports the status of its internal links."""
    relative_file_path = os.path.relpath(file_path, DOCS_ROOT)
    logger.info(f"--- Checking: {relative_file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Could not read file {relative_file_path}. Error: {e}")
        return

    file_dir = os.path.dirname(file_path)
    found_issues = False

    for match in LINK_REGEX.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2).strip()

        if not link_target or '#' in link_target.split('/')[-1]: # Ignore empty links or links with anchors for now
             continue

        # We are only interested in links to other markdown files for this check
        if not link_target.endswith('.md'):
            logger.debug(f"Ignoring non-markdown link: '{link_target}'")
            continue

        # Path if the link is root-relative (relative to DOCS_ROOT)
        root_relative_path_check = os.path.normpath(os.path.join(DOCS_ROOT, link_target))
        is_valid_as_root_relative = os.path.exists(root_relative_path_check)

        # Path if the link is file-relative (relative to the file it's in)
        file_relative_path_check = os.path.normpath(os.path.join(file_dir, link_target))
        is_valid_as_file_relative = os.path.exists(file_relative_path_check)

        if is_valid_as_root_relative:
            logger.debug(f"Link '{link_target}' is CORRECT.")
        elif is_valid_as_file_relative:
            correct_path = os.path.relpath(file_relative_path_check, DOCS_ROOT).replace('\\', '/')
            logger.warning(f"[NEEDS FIX]: Link '[{link_text}]({link_target})' should be '[{link_text}]({correct_path})'")
            found_issues = True
        else:
            logger.error(f"[BROKEN]: Link '[{link_text}]({link_target})' is invalid. Target not found.")
            found_issues = True

    if not found_issues:
        logger.info("No issues found in this file.")

def main():
    """Main function to walk through the docs directory and check all markdown files."""
    logger.info(f'Starting link analysis in: {DOCS_ROOT}')
    for root, _, files in os.walk(DOCS_ROOT):
        for file in files:
            if file.endswith('.md'):
                check_links_in_file(os.path.join(root, file))
    logger.info('--- Analysis Complete ---')

if __name__ == '__main__':
    main()
