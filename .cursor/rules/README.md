# Cursor Rules

This directory contains project-specific rules and configurations for the Cursor IDE.

## Files

- `default.json`: Contains the main configuration rules for:
  - Python code style and conventions
  - JavaScript formatting preferences
  - Docker best practices
  - General editor settings

## Rule Descriptions

### Python Rules
- Max line length: 88 characters (Black formatter compatible)
- Indentation: 4 spaces
- Naming conventions follow PEP 8

### JavaScript Rules
- Max line length: 80 characters
- Indentation: 2 spaces
- Semicolons required

### Docker Rules
- Prefer official base images
- Encourage multi-stage builds for optimization

### General Rules
- Trim trailing whitespace
- Ensure final newline
- UTF-8 encoding

## Updating Rules

To modify these rules, edit the corresponding JSON file. Changes will be applied to new Cursor sessions. 