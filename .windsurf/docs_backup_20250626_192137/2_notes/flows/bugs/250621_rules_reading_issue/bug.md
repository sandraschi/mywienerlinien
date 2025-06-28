# Bug: Windsurf Fails to Read and Apply Rules Initially

## Description
When first interacting with the system, Windsurf does not properly read or apply the user's rules and memories until explicitly prompted to do so.

## Steps to Reproduce
1. Start a new conversation
2. Make a request without explicitly mentioning rules
3. Observe that the initial responses don't follow the required format

## Expected Behavior
- Windsurf should automatically read and apply all user rules and memories at the start of every interaction
- All responses should include the required "lgr1 lgr2" prefix
- The system should enforce all formatting and behavior rules from the beginning

## Actual Behavior
- Initial responses don't include the required prefixes
- Rules are only acknowledged after being explicitly prompted
- Multiple interactions are needed to get proper rule compliance

## Environment
- System: Windows
- Time of Report: 2025-06-21 18:00:52+02:00
