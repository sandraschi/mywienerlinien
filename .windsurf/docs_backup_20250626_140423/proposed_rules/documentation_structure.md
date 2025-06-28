# Documentation Structure Rules

## 1. Directory Structure
All documentation must follow this structure:

```
docs/
├── 1_news/                      # News and announcements
├── 2_notes/                     # Personal and project notes
├── 3_ai/                        # AI-related documentation
│   ├── companies/               # AI companies and technologies
│   ├── persons/                 # Key people in AI
│   ├── opinion/                 # Opinion pieces on AI
│   └── news/                    # AI news and updates
├── 4_development/               # Core development docs
├── 5_dev_tools/                 # Development tools
│   └── windsurf/                # Windsurf documentation
└── 6_tools/                     # Other tools and utilities
```

## 2. Naming Conventions
- Use lowercase with underscores for directory names
- Prefix top-level directories with numbers for ordering
- Keep file and directory names short but descriptive

## 3. File Organization
- Place related files in dedicated directories
- Use README.md in each directory to explain its purpose
- Keep individual markdown files focused on a single topic

## 4. Version Control
- The `docs_stable/` directory contains the latest stable version
- The `docs/` directory contains the development version
- Both directories must maintain the same structure

## 5. Migration Process
1. Create a backup using `backup-docs.ps1`
2. Run `migrate-docs.ps1` to reorganize content
3. Verify all links and references
4. Test the documentation locally
5. Deploy changes to the stable version after review
