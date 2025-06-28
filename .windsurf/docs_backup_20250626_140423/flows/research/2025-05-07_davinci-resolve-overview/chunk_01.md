# DaVinci Resolve: API, Scripting, Extensions, AI, and Platform Overview

## What is DaVinci Resolve?
DaVinci Resolve is a professional video editing, color grading, VFX, and audio post-production suite by Blackmagic Design. It is widely used in film, TV, and YouTube production.

---

## Pricing and Editions
| Edition                 | Price           | Platforms                  | Scripting/API | AI Features        |
|-------------------------|-----------------|----------------------------|---------------|--------------------|
| Resolve (Free)          | $0              | Win, macOS, Linux          | Python/Lua    | Basic (Magic Cut)  |
| Resolve Studio (Paid)   | $295 (one-time) | Win, macOS, Linux          | Python/Lua    | Advanced (Magic Mask, etc.) |

- **Free version** is extremely capable and scriptable.
- **Studio** is a one-time purchase (not a subscription), includes advanced AI and high-end features.
- All platforms are supported (best support on Windows/macOS).

---

## Platforms
- **Windows** (10/11, 64-bit)
- **macOS** (Intel & Apple Silicon)
- **Linux** (CentOS/RHEL, some Ubuntu support; Studio officially for Linux)

---

## API, Scripting, and Extensions
- **Python & Lua scripting API** (available in both Free and Studio):
  - Automate timeline edits, media import/export, render jobs, color grading, and more.
  - TCP server for remote scripting (can build REST/MCP bridges).
- **Installable Extensions:**
  - Custom panels, effects, and integrations via Developer API.
  - Third-party plugins for VFX, workflow, and more.
