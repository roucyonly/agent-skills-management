---
name: maintain
description: "Maintain skills: find similar skills to merge, suggest deprecation for unused ones, compact usage logs, clean registry. Use when user wants to organize, clean up, or optimize their skill portfolio."
---

# Skill Maintenance

## What to do

Ask the user which task they want, or run all four if they say "full maintenance":

### Task 1: Deprecation Suggestions

1. Read `usage.jsonl` and `registry.json`
2. For each registered skill with `status: "active"`:
   - Count invocations in the last 90 days
   - If 0 invocations → **deprecation candidate**
   - If success rate < 50% with 5+ invocations → **review candidate**
3. Present the list:
   ```
   Deprecation candidates (unused 90+ days):
   - old-skill: Last used 2026-02-01. Description: ...

   Review candidates (low success rate):
   - buggy-skill: 40% success rate (6 invocations)
   ```
4. **Ask user to confirm** before changing any status
5. To deprecate: set skill status to "deprecated" in registry.json

### Task 2: Merge/Similarity Suggestions

1. Read `registry.json` to get all skill names and paths
2. Read each active skill's SKILL.md file completely
3. **Compare skills pairwise** using your semantic understanding:
   - Do the names share common words or themes? (e.g., "web-scraper" vs "web-automation")
   - Do the descriptions describe overlapping capabilities?
   - Is the instruction content significantly overlapping?
   - Do they share tags?
4. For each pair with high overlap (>70%):
   - Show a side-by-side comparison
   - Explain why they are similar
   - Suggest which to keep and which to absorb
   - **Ask user to confirm** before merging
5. To merge a skill:
   - Read both SKILL.md files
   - Combine the best parts into the kept skill's SKILL.md
   - Set the absorbed skill's status to "merged_into:<kept-skill-name>" in registry.json
   - Optionally remove the absorbed skill's SKILL.md file

### Task 3: Usage Log Compaction

1. Check if `usage.jsonl` has more than 5000 lines
2. If so:
   - Keep the most recent 1000 lines as raw events
   - Aggregate older data into a summary line at the top:
     ```json
     {"event":"summary","ts":"<now>","period_start":"<earliest>","period_end":"<latest>","skills":{"skill-name":{"invocations":N,"successes":N,"failures":N,"avg_duration_s":N}}}
     ```
   - Write the compacted file

### Task 4: Registry Cleanup

1. Find skills with `status: "missing"` for more than 30 days
2. Present them to the user
3. **Ask user to confirm** before removing
4. Remove confirmed entries from registry.json

## Important Rules

- **Always ask for user confirmation** before deleting, merging, or deprecating any skill
- Back up SKILL.md files before modifying them (copy to `<name>.SKILL.md.bak`)
- When suggesting merges, always explain the reasoning
- Log what changes were made at the end
