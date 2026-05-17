---
name: scan
description: "Scan directories to discover and register skills. Use when user wants to find, register, or update skills in the registry."
---

# Skill Scanner

## What to do

1. **Scan these directories for SKILL.md files:**
   - `~/.claude/plugins/local/skills/*/SKILL.md` (local plugin skills)
   - `.claude/skills/*/SKILL.md` (current project skills)
   - If the user specifies additional paths, scan those too

2. **For each SKILL.md found:**
   - Read the file content
   - Parse YAML frontmatter (content between the first two `---` markers)
   - Extract: `name`, `description`, `tags`, `version`

3. **Read the current registry** from `~/.claude/skills-management/data/registry.json`

4. **Update the registry:**
   - **New skills**: Found in scan but not in registry → add with `status: "active"`
   - **Updated skills**: Skill exists but metadata (description, tags) changed → update fields
   - **Missing skills**: In registry but SKILL.md no longer exists → set `status: "missing"`
   - Do NOT remove entries — only change status to "missing"

5. **Write the updated registry** back to `~/.claude/skills-management/data/registry.json`
   - Update `last_updated` timestamp
   - Sort skills alphabetically by name

6. **Report results:**
   ```
   Scan complete:
   - New: 3 skills registered
   - Updated: 1 skill updated
   - Missing: 1 skill marked as missing
   - Total: 5 skills in registry
   ```

## registry.json schema

```json
{
  "version": 1,
  "last_updated": "ISO-8601 timestamp",
  "skills": {
    "skill-name": {
      "name": "skill-name",
      "description": "What this skill does",
      "path": "absolute path to SKILL.md",
      "source": "local",
      "tags": ["tag1", "tag2"],
      "status": "active|missing",
      "registered_at": "ISO-8601 timestamp"
    }
  }
}
```

## Important
- Always read the current registry before modifying it
- Write the complete file (not partial updates)
- If registry.json does not exist, create it with the schema above
- The `source` field should be "local" for plugin skills, "project" for project-level skills
