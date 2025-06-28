# Notion Databases

## Overview
Notion databases are powerful tools for organizing and visualizing information. They combine the functionality of spreadsheets with the flexibility of a database, allowing you to create custom views, filters, and relationships between different pieces of content.

## Database Properties

### Property Types

| Type | Description | Example |
|------|-------------|---------|
| **Text** | Simple text field | "Project Name" |
| **Number** | Numeric values | 42, 3.14 |
| **Select** | Single-select dropdown | "In Progress" |
| **Multi-select** | Multiple-select dropdown | ["Design", "Development"] |
| **Date** | Date and time | 2025-06-28 |
| **People** | Team members | @JohnDoe |
| **Files & Media** | Attachments | [image.png] |
| **Checkbox** | Boolean toggle | ☑️ |
| **URL** | Web address | https://example.com |
| **Email** | Email address | user@example.com |
| **Phone** | Phone number | +1 (555) 123-4567 |
| **Formula** | Computed value | CONCATENATE(prop("First"), " ", prop("Last")) |
| **Relation** | Link to another database | [Related Project] |
| **Rollup** | Aggregate related data | SUM(prop("Hours")) |
| **Created time** | Automatic timestamp | 2025-06-28T10:00:00Z |
| **Last edited time** | Automatic timestamp | 2025-06-28T11:30:00Z |
| **Created by** | User who created | @System |
| **Last edited by** | Last editor | @JaneDoe |

### Creating Properties

1. Open a database
2. Click `+` next to the last column
3. Select property type
4. Configure the property settings

## Database Views

### View Types

#### Table View
- Spreadsheet-like interface
- Sort and filter rows
- Group by any property

#### Board View (Kanban)
- Cards organized in columns
- Drag and drop between statuses
- Group by select or status property

#### Calendar View
- Events on a calendar
- Drag to reschedule
- Filter by date range

#### Gallery View
- Visual card layout
- Great for portfolios or catalogs
- Custom cover images

#### List View
- Simple, linear list
- Expandable to show details
- Compact view of items

#### Timeline View
- Gantt-style visualization
- Track project schedules
- Dependencies between items

### Creating Views

1. Click `+ Add a view`
2. Choose view type
3. Configure view settings
4. Set as default if needed

## Database Relations

### Creating Relations

1. Add a `Relation` property
2. Select target database
3. Choose relation type:
   - Single property
   - Two-way (synchronized)

### Example: Tasks and Projects

**Tasks Database**
- Name: Task name
- Project: Relation to Projects
- Status: Select
- Due Date: Date

**Projects Database**
- Name: Project name
- Tasks: Relation to Tasks
- Status: Select
- Timeline: Date range

## Database Formulas

### Common Formulas

```javascript
// Concatenation
prop("First Name") + " " + prop("Last Name")

// Date calculations
dateBetween(prop("Due Date"), now(), "days")

// Conditional logic
if(prop("Priority") == "High", "🔴", "⚪")

// Math operations
(prop("Hours") * prop("Rate")) * (1 - prop("Discount"))

// Text manipulation
slice(prop("Description"), 0, 100) + "..."
```

### Formula Functions

| Category | Functions |
|----------|-----------|
| **Text** | `concat()`, `format()`, `replaceAll()`, `test()`, `empty()` |
| **Numbers** | `abs()`, `ceil()`, `floor()`, `round()`, `mod()` |
| **Dates** | `now()`, `timestamp()`, `fromTimestamp()`, `dateBetween()` |
| **Logic** | `if()`, `==`, `!=`, `>`, `<`, `>=`, `<=`, `and()`, `or()`, `not()` |
| **Arrays** | `map()`, `filter()`, `find()`, `contains()`, `join()` |

## Database Templates

### Creating Templates

1. Click `New` dropdown
2. Select `New template`
3. Configure template properties
4. Add default content

### Example: Meeting Notes

```markdown
# {{Meeting Name}}

**Date:** {{date}}
**Attendees:** {{people}}
**Related to:** {{relation}}

## Agenda
- [ ] 

## Notes

## Action Items
- [ ] 
```

## Advanced Features

### Linked Databases

1. Type `/linked`
2. Select source database
3. Apply filters/sorts
4. Save as a new view

### Database Locking

1. Click `•••` menu
2. Select `Lock database`
3. Set permissions

### Export Options

1. Click `•••` menu
2. Select `Export`
3. Choose format:
   - Markdown
   - HTML
   - PDF
   - CSV (for tables)

## Best Practices

### Naming Conventions
- Use consistent property names
- Prefix related databases (e.g., `prj_`, `task_`)
- Use title case for view names

### Performance
- Limit relation depth
- Use rollups for common calculations
- Archive old items

### Collaboration
- Use @mentions in properties
- Set up notifications
- Use comments for discussions

## Troubleshooting

### Common Issues
- **Missing relations**: Check property settings
- **Formula errors**: Verify data types
- **Slow performance**: Reduce view complexity

### Resources
- [Notion Formulas Documentation](https://www.notion.so/help/formulas)
- [Notion Template Gallery](https://www.notion.so/Notion-Template-Gallery-181e961aeb5c4ee6915307c0dfd5156d)
- [Notion API Documentation](https://developers.notion.com/)

## Last Updated
2025-06-28 01:30:00

*This file was last updated manually.*
