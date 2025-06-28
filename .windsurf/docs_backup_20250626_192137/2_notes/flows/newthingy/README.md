# Annoyinator Meta-Build Flow: From User Idea to Rulebook-Compliant Extension

## Overview
This directory documents the meta-agentic flow for building new features, sites, and extensions in Annoyinator/Windsurf/Cascade, even with current LLM and agent limitations.

## The Problem
- Local LLMs (like Ollama) and current agentic tools (Cascade, etc.) have **limited context windows** and **no project-specific long-term memory**.
- These tools cannot fully ingest the project structure, rulebook, or prior flows automatically.
- Direct, one-click AI building is not yet possible—especially for complex, rulebook-compliant extensions.

## The Meta Solution: Builder Instructions & Human-in-the-Loop

### 1. **User Plans a New Thing**
  - The user describes their new site/feature (e.g., "beekeeper website") using the `/site_configurator` or a similar UI.
  - The configurator generates a **builder instruction**: a markdown document with all required context, best practices, and rulebook references.

### 2. **Builder Instruction is Saved and/or Presented**
  - The builder instruction is saved in a new directory: `docs/flows/newthingy/YYYY-MM-DD_<site-name>/builder.md`.
  - It is also displayed to the user for copy-paste as a prompt for Cascade or another agent.

### 3. **Cascade (or Agent) Reads & Builds**
  - Cascade is pointed to the builder.md or receives the instruction as a prompt.
  - Cascade reads the instruction, checks the Annoyinator rulebook (`docs/rules.md`), and scaffolds the new extension.
  - All actions are tracked in the newthingy flow directory for transparency and reproducibility.

### 4. **Meta-Feedback & Iteration**
  - The user can review, edit, or refine the builder instruction before running it.
  - The process is transparent, editable, and can be iterated on as tools improve.

## Why This Works
- **Rulebook compliance:** All flows reference and follow `docs/rules.md`.
- **No LLM hallucination:** Instructions are generated from known project context and best practices.
- **Human-in-the-loop:** The user can review and edit before Cascade acts.
- **Scalable:** As LLMs and agents improve, this workflow will become more seamless and powerful.

## The Future: Small World Builder
- Once LLMs/agents can ingest the full project, rulebook, and flows, and have persistent long-term memory, this system can become a true **small world builder**:
  - Users will describe their intent in natural language.
  - The agent will ingest all context, generate a plan, and execute it end-to-end (including hardware/robotics integration).
  - The system will be able to build, deploy, and control not just software, but the physical world—intelligently and safely.

## For Now
- Use the configurator and builder instruction flow as a meta, transparent, and rulebook-compliant bridge between user intent and project extension.
- Paste the builder instruction into Cascade or save as `builder.md` in a newthingy directory.
- As tools improve, this workflow will become ever more powerful and agentic.

---

*"In more capable hands than mine, this will be a true small world builder."*
