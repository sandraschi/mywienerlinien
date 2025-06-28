# Drone Mission Control

## Purpose
Coordinate drones for whimsical, peaceful missions: skywriting, banner towing, or even a synchronized "fart at the annoying neighbor" (good-natured, non-offensive, and with consent).

## API Design (Draft)
- POST /api/drone_mission
    - mission_type: string ("skywriting", "banner", "sound_effect")
    - location: string
    - payload: string (e.g. banner text, sound file)
    - duration: int (seconds)
    - consent_required: bool

## Safety and Consent
- All drone flights require explicit human approval and compliance with local laws
- No flights in restricted or sensitive airspace
- Payload content must be reviewed for safety and tone

## To Do
- Simulation/test harness for drone missions
- Consent workflow integration
- Logging and audit
