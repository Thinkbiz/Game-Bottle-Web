# Cursor Rules for Game-Bottle-Web

This directory contains the cursor rules for maintaining code quality and preventing common issues in the Game-Bottle-Web project.

## Rules Categories

1. [Database Rules](rules/database.rules.json)
2. [Event Tracking Rules](rules/event-tracking.rules.json)
3. [UI Rules](rules/ui.rules.json)
4. [Monitoring Rules](rules/monitoring.rules.json)
5. [Error Handling Rules](rules/error-handling.rules.json)
6. [State Management Rules](rules/state.rules.json)
7. [Mobile Optimization Rules](rules/mobile.rules.json)
8. [Performance Rules](rules/performance.rules.json)
9. [API Rules](rules/api.rules.json)
10. [Security Rules](rules/security.rules.json)
11. [Development Workflow Rules](rules/development.rules.json)
12. [Documentation Rules](rules/documentation.rules.json)

## Implementation

These rules are enforced through Cursor's rule engine. Each rule file contains specific patterns and anti-patterns that Cursor will use to guide development.

## Usage

Cursor will automatically enforce these rules while coding. You'll see suggestions and warnings based on these rules as you work.

## Updating Rules

To update these rules:
1. Edit the relevant rule file in the `.cursor/rules/` directory
2. Commit and push the changes
3. Cursor will automatically pick up the new rules

## Rule Format

Each rule file follows this format:
```json
{
  "rules": [
    {
      "name": "Rule Name",
      "description": "Rule description",
      "pattern": "What to look for",
      "antiPattern": "What to avoid",
      "severity": "error|warning|info"
    }
  ]
}
``` 