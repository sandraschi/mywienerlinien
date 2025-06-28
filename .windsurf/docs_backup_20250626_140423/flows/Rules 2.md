# Agentic Coding Rules: Bug and Research Tokens

## About Rulebooks in Windsurf IDE (and Agentic IDEs)

- **Rulebooks** allow you to define, document, and automate project-specific workflows, coding standards, and meta-procedures for agentic coding environments like Windsurf IDE.
- Rulebooks can be used to:
  - Standardize bug and research handling, code review, onboarding, and more.
  - Enable AI agents to follow custom project protocols automatically.
  - Serve as meta-rulebooks for higher-level project governance or automation.
- **Best practices:**
  - Place your main rulebook in `docs/rules.md` or a similarly prominent location in your repo.
  - For multi-project or meta rules, use `docs/meta-rules.md` or `docs/flows/rules.md`.
  - Reference rulebooks in your onboarding docs and README for new contributors and agents.

**Enabling Rulebook Usage in a New Cascade Session:**
- Shortest prompt: `Use docs/rules.md as the agentic rulebook for bug and research flows.`
- To reload the rules and begin using them, you can also say: `Read and memorize docs/rules.md as the rulebook for handling bug:...:bug and research:...:research tokens in this project.`
- **Note:** Session memory is not persistent. You must reload or reference the rulebook in each new session to enable agentic flows.


## 1. Bug Handling Rules (`bug: ... :bug`)
- The token `bug:` starts a bug description, and `:bug` ends it.
- When a bug block is encountered:
  1. You must research the bug (whatever it is) thoroughly.
  2. Place the bug description and your analysis in two separate files, in a new directory under `docs/flows/bugs/`.
     - Directory name format: `YYYY-MM-DD_short-description` (use the current date and a concise bug name).
     - Example files: `bug.md` (the original bug description), `analysis.md` (your analysis and findings).
  3. Follow the structure of existing entries in `docs/flows/bugs/` for formatting and organization.

## 2. Research Handling Rules (`research: ... :research`)
- The token `research:` starts a research request, and `:research` ends it.
- When a research block is encountered:
  1. Research the topic as thoroughly as possible.
  2. Place the research results in a new subdirectory under `docs/flows/research/`. (If this directory does not exist, create it.)
     - Directory name format: `YYYY-MM-DD_short-topic` (use the current date and a concise topic name).
     - Research results should be split into multiple markdown files for each section (do not use the word 'chunk' in headlines; chunking is an internal mechanism).
     - Each section must be at least 50 lines, written in thorough, readable paragraphs (not just lists of oneliners).
     - Follow the formatting, structure, and depth of existing research entries in `docs/research/` (currently misplaced, but to be used as examples).
  3. Each section should be well-structured, with clear headlines and references as needed.
  4. For every research flow, automatically generate:
     - A single-file HTML webpage combining all sections with good formatting
     - A .docx document combining all sections, properly formatted


## 3. Links and Other Flows
- For other tokens such as `links:` or `:links`, or analogous flows, consult the structure and rules in the `docs/flows/` directory and follow their conventions.

---

research: user provided rulebooks in windsurf ide, tips and tricks, best placement of rulebooks and meta rulebooks, example rulebooks found on the web, comparison to other agentic ides handling rules :research

---

**Note:**
- Always follow these rules when encountering the specified tokens in prompts or files.
- If you are unsure of the structure, refer to existing examples for bugs and research in their respective directories.
- These rules are mandatory for all future work involving bug and research tokens.
- **Prompt structure:** If you want to trigger a research or bug flow, it should be the very first thing in your prompt. If you include multiple requests in one prompt, only the first (the flow request) is guaranteed to be processed—subsequent requests may be ignored.
