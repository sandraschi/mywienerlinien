# chunk_03: Tips, Tricks, and Best Placement for Rulebooks & Meta-Rulebooks

## Tips & Tricks
- **Keep Rulebooks Modular:** Separate project-specific rules (`docs/rules.md`) from organization-wide or meta-rules (`docs/meta-rules.md`).
- **Version Control:** Always track rulebooks in your main repo for transparency and collaboration.
- **Reference in Onboarding:** Link rulebooks in your README and onboarding guides so new contributors and agents know where to find them.
- **Use Token Blocks:** Clearly mark agentic flows with tokens (e.g., `bug: ... :bug`) for easy parsing and automation.
- **Document Meta-Rules:** For multi-project or cross-team consistency, maintain a `docs/meta-rules.md` or `docs/flows/rules.md`.
- **Automate Rulebook Loading:** Use project templates or scripts to remind users/agents to load rulebooks at session start.

## Best Placement
- **Project Rulebook:** `docs/rules.md`
- **Meta-Rulebook:** `docs/meta-rules.md` or `docs/flows/rules.md`
- **Specialized Flows:** Under `docs/flows/` (e.g., `docs/flows/bugs/`, `docs/flows/research/`)

## Strategies for Meta-Rulebooks
- **Hierarchy:** Use meta-rulebooks for organization-wide policies, with project rulebooks for specifics.
- **Inheritance:** Allow project rulebooks to override or extend meta-rules as needed.

## Next Chunk
- Synthesis and recommendations for rulebook-driven agentic workflows in Windsurf and similar IDEs.
