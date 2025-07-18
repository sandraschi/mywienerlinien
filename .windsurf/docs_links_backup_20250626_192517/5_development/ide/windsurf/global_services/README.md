﻿# Windsurf Global Services Documentation

## Overview

Windsurf provides a set of global services that are available across all repositories. These services are accessed through the `.windsurf/` directory in your repository root.

## Documentation Structure

1. [Logging System](/ide/windsurf/global_services/./logging_system.md)
2. [Rulebooks](/ide/windsurf/global_services/./rulebooks.md)
3. [Configuration Store](/ide/windsurf/global_services/./config_store.md)
4. [Template Library](/ide/windsurf/global_services/./template_library.md)
5. [Shared Libraries](/ide/windsurf/global_services/./shared_libraries.md)
6. [Documentation Hub](/ide/windsurf/global_services/./documentation_hub.md)
7. [Task Management](/ide/windsurf/global_services/./task_management.md)
8. [Cache System](/ide/windsurf/global_services/./cache_system.md)
9. [Documentation Standards](/ide/windsurf/global_services/./documentation_standards.md)
10. [Multi-Developer Setup](/ide/windsurf/global_services/./multi_developer_setup.md)

## Accessing Global Services

### Single Developer Setup
All global services are accessible from any repository with a `.windsurf` directory. The services are designed to work together seamlessly while maintaining security and isolation between projects.

### Multi-Developer Environment
For teams, we recommend setting up a centralized server with secure access via Tailscale VPN. See [Multi-Developer Setup](/ide/windsurf/global_services/./multi_developer_setup.md) for detailed instructions on:
- Centralized service architecture
- Network configuration with Tailscale
- Security implementation
- Developer workstation setup
- Monitoring and SIEM integration

## Versioning

Global services follow semantic versioning (SemVer) where applicable. Each service's version is tracked independently.

## Contributing

To contribute to global services, follow the contribution guidelines in the [Windsurf Core Repository](https://github.com/windsurf-ai/core).

---
*Last Updated: 2025-06-23*

