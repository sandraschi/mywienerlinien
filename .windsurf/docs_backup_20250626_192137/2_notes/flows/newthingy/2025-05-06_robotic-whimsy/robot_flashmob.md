# Robot Flashmob Orchestration

## Purpose
Deploy and coordinate robots to perform whimsical, peaceful flashmobs in public or private spaces. Example: robots with placards saying "Robots are people! Don't tread on us!"

## API Design (Draft)
- POST /api/robot_flashmob
    - scenario: string (e.g. "protest", "dance", "parade")
    - location: string (GPS or description)
    - placard_texts: [string]
    - robot_count: int
    - consent_required: bool

## Safety and Consent
- All actions require explicit human approval
- No deployment in sensitive or restricted areas
- Placard content must be reviewed for safety and tone

## To Do
- Simulation harness for flashmob scenarios
- Consent workflow integration
- Logging and audit
