#!/usr/bin/env python3
"""
Configurable Repository Backup Script

This script backs up multiple git repositories based on a configuration file.
It creates timestamped ZIP archives and maintains a configurable number of backups.
"""

import os
import sys
import json
import zipfile
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

class BackupConfig:
    """Handle backup configuration loading and validation."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load and validate the configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self._validate_config()
            
            # Set up file logging if specified
            if 'log_file' in self.config and self.config['log_file']:
                file_handler = logging.FileHandler(
                    self.config['log_file'],
                    mode='a',
                    encoding='utf-8'
                )
                file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                )
                logger.addHandler(file_handler)
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _validate_config(self) -> None:
        """Validate the configuration structure and values."""
        required_keys = ['backup_root', 'repositories']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")
        
        for repo in self.config['repositories']:
            if 'name' not in repo or 'path' not in repo:
                raise ValueError("Each repository must have 'name' and 'path' specified")
            
            repo_path = Path(repo['path'])
            if not repo_path.exists():
                logger.warning(f"Repository path does not exist: {repo_path}")
            
            # Set default values if not specified
            repo.setdefault('enabled', True)
            repo.setdefault('exclude_dirs', [])
            repo.setdefault('exclude_extensions', [])


class RepositoryBackup:
    """Handle backing up a single repository."""
    
    def __init__(self, config: Dict[str, Any], global_config: Dict[str, Any]):
        self.name = config['name']
        self.path = Path(config['path'])
        self.enabled = config['enabled']
        self.exclude_dirs = set(config.get('exclude_dirs', []))
        self.exclude_extensions = set(config.get('exclude_extensions', []))
        self.backup_root = Path(global_config['backup_root'])
        self.max_backups = global_config.get('max_backups_per_repo', 5)
    
    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from backup."""
        # Check if any parent directory is in exclude_dirs
        for part in path.parts:
            if part in self.exclude_dirs:
                return True
        
        # Check file extensions
        if path.suffix.lower() in self.exclude_extensions:
            return True
            
        return False
    
    def create_backup(self) -> Optional[Path]:
        """Create a backup of the repository."""
        if not self.enabled:
            logger.info(f"Skipping disabled repository: {self.name}")
            return None
            
        if not self.path.exists():
            logger.error(f"Repository path does not exist: {self.path}")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / self.name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"{self.name}_backup_{timestamp}.zip"
        
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.path):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                    
                    for file in files:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(self.path)
                        
                        if not self.should_exclude(file_path):
                            zipf.write(file_path, rel_path)
                            
            logger.info(f"Created backup: {backup_file}")
            self._cleanup_old_backups()
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup for {self.name}: {e}")
            return None
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backups, keeping only the most recent max_backups."""
        backup_dir = self.backup_root / self.name
        if not backup_dir.exists():
            return
            
        backups = sorted(
            backup_dir.glob(f"{self.name}_backup_*.zip"),
            key=os.path.getmtime
        )
        
        while len(backups) > self.max_backups:
            old_backup = backups.pop(0)
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.error(f"Failed to remove old backup {old_backup}: {e}")


def main():
    """Main function to run the backup process."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    config_path = script_dir / "backup_config.json"
    
    # Load configuration
    try:
        config = BackupConfig(config_path)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Process each repository
    success_count = 0
    for repo_config in config.config['repositories']:
        try:
            repo = RepositoryBackup(repo_config, config.config)
            if repo.create_backup() is not None:
                success_count += 1
        except Exception as e:
            logger.error(f"Error processing repository {repo_config.get('name', 'unknown')}: {e}")
    
    logger.info(f"Backup completed. Successfully backed up {success_count} repositories.")
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
