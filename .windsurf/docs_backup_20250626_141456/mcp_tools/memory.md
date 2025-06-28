# MCP Tool: Memory

## Overview
The `memory` server provides the agent with a long-term memory system structured as a knowledge graph. This allows the agent to create, retrieve, update, and delete information about entities and the relationships between them. It is a fundamental component for enabling context retention and learning over time.

Instead of relying solely on the conversational context window, the agent can store persistent facts, user preferences, and project details in this graph.

## Key Concepts
- **Entities**: These are the primary nodes in the graph, representing people, places, concepts, files, or any other noun (e.g., `OpenAI`, `app.py`, `Sam Altman`).
- **Observations**: These are facts or pieces of data associated with an entity (e.g., an observation for the `OpenAI` entity could be "Founded in 2015").
- **Relations**: These are the directed edges that connect entities, describing how they are related (e.g., `Sam Altman` -[IS_CEO_OF]-> `OpenAI`).

## Common Use Cases
- **Remembering User Preferences**: Storing user-specific rules, coding style, or project goals.
- **Mapping Codebases**: Creating a mental model of a software project by linking files, functions, and classes.
- **Retaining Project Context**: Keeping track of key decisions, architectural patterns, and important figures related to a project.
- **Learning from Interactions**: Building a knowledge base from user instructions and feedback.

## Example Workflow: Storing Information about a Project

1.  **Create entities for the project and a key file:**
    ```xml
    <mcp5_create_entities>
    {
        "entities": [
            {
                "name": "Windsurf Project",
                "entityType": "Project",
                "observations": ["A project to document AI companies."]
            },
            {
                "name": "docs/ai/companies/openai.md",
                "entityType": "File",
                "observations": ["Contains documentation for OpenAI."]
            }
        ]
    }
    </mcp5_create_entities>
    ```

2.  **Create a relation to link the file to the project:**
    ```xml
    <mcp5_create_relations>
    {
        "relations": [
            {
                "from": "docs/ai/companies/openai.md",
                "to": "Windsurf Project",
                "relationType": "IS_PART_OF"
            }
        ]
    }
    </mcp5_create_relations>
    ```

3.  **Search for nodes related to "OpenAI":**
    ```xml
    <mcp5_search_nodes>
    {
        "query": "OpenAI"
    }
    </mcp5_search_nodes>
    ```

## Available Tools
Key tools include `create_entities`, `create_relations`, `add_observations`, `search_nodes`, and `delete_entities`. For a full list, use the `list_resources` tool on the `memory` server.

```xml
<list_resources>
{
    "ServerName": "memory"
}
</list_resources>
```
