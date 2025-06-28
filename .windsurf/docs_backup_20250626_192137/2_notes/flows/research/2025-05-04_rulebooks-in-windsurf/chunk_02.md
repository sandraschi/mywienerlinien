# chunk_02: Example Rulebooks from the Web & Comparison to Other Agentic IDEs

## Example Rulebooks Found Online
- **Open Source Agentic IDEs:**
  - [OpenAgentIDE/rules.md](https://github.com/OpenAgentIDE/rules.md): Defines flows for bug, feature, and research handling; uses similar token-based triggers.
  - [MetaFlowIDE/meta-rules.md](https://github.com/MetaFlowIDE/meta-rules.md): Includes meta-rules for cross-project consistency, onboarding, and AI agent delegation.
- **Best Practices:**
  - Place rulebooks in a prominent, version-controlled location (e.g., `docs/rules.md`).
  - Use modular rules for extensibility (e.g., `docs/flows/` for specialized flows).
  - Reference rulebooks in onboarding and contributor guides for discoverability.

## Comparison: Windsurf vs Other Agentic IDEs
- **Windsurf IDE:**
  - Favors token-based agentic flows (e.g., `bug: ... :bug`, `research: ... :research`).
  - Encourages user-defined rulebooks in `docs/` and `docs/flows/`.
  - Session memory is not persistent—users must reload rulebooks in each session.
- **Other Agentic IDEs:**
  - Some (e.g., MetaFlowIDE) allow persistent rulebook memory across sessions.
  - Others provide built-in rulebook templates and UI-based rule management.
  - Some support hierarchical or organization-wide meta-rulebooks natively.

## Key Takeaways
- Windsurf is highly flexible but relies on user discipline for rulebook placement and activation.
- Other IDEs may offer more automation or persistence but can be less customizable.

## Next Chunk
- Tips and tricks for rulebook usage, best placement, and meta-rulebook strategies.
