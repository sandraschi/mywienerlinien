# Repository Backup Script

A configurable Python script to back up multiple Git repositories to timestamped ZIP archives.

## Features

- Backs up multiple repositories defined in a JSON config file
- Excludes specified directories and file extensions
- Maintains a configurable number of backups per repository
- Detailed logging to both console and file
- Handles errors gracefully with meaningful messages
- Supports Windows Task Scheduler for automated backups

## Requirements

- Python 3.6 or higher
- No additional Python packages required (uses only standard library)

## Configuration

1. Edit the `backup_config.json` file to configure your backups:

```json
{
  "backup_root": "D:\\Backups",
  "log_file": "D:\\Backups\\backup_log.txt",
  "max_backups_per_repo": 5,
  "repositories": [
    {
      "name": "wienerlinien",
      "path": "D:\\Dev\\repos\\mywienerlinien",
      "enabled": true,
      "exclude_dirs": ["venv", ".git", "__pycache__", "node_modules"],
      "exclude_extensions": [".pyc", ".pyo", ".pyd", ".log", ".tmp"]
    }
  ]
}
```

### Configuration Options

- `backup_root`: Base directory where backups will be stored
- `log_file`: Path to the log file (set to empty string to disable file logging)
- `max_backups_per_repo`: Maximum number of backups to keep per repository (oldest are deleted first)
- `repositories`: List of repositories to back up
  - `name`: Short name for the repository (used in backup filenames)
  - `path`: Full path to the repository
  - `enabled`: Set to `false` to skip this repository
  - `exclude_dirs`: List of directory names to exclude
  - `exclude_extensions`: List of file extensions to exclude

## Usage

### Manual Run

```powershell
# Run the backup script
python scripts/backup/backup_script.py
```

### Scheduled Task (Windows)

1. Open Task Scheduler
2. Create a new task
3. Set the trigger to "Daily" and configure to repeat every 4 hours
4. Set the action to:
   - Program/script: `pythonw.exe`
   - Add arguments: `"D:\Dev\repos\mywienerlinien\scripts\backup\backup_script.py"`
   - Start in: `D:\Dev\repos\mywienerlinien`
5. Set the task to run whether the user is logged in or not
6. Save the task

## Testing

1. Run the script manually to verify it works:
   ```powershell
   python scripts/backup/backup_script.py
   ```
2. Check the backup directory for the new backup
3. Check the log file for any errors

## Logging

Logs are written to both the console and the specified log file. Each log entry includes:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Message

## Error Handling

The script will:
- Skip repositories that don't exist
- Log errors but continue with other repositories
- Create backup directories if they don't exist
- Handle file permission errors gracefully

## Adding More Repositories

To add more repositories, simply add more entries to the `repositories` array in `backup_config.json`.

## License

This script is provided as-is under the MIT License.
