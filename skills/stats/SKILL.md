---
name: stats
description: "Show skill usage statistics and trends. Use when user asks about how often skills are used, which are most popular, or overall usage patterns."
---

# Skill Usage Statistics

## What to do

1. **Read the usage log** from `~/.claude/skills-management/data/usage.jsonl`
   - Each line is a JSON event
   - `skill_start` events: `{"event":"skill_start","ts":"...","session_id":"...","skill":"...","source":"tool"}`
   - `skill_end` events: `{"event":"skill_end","ts":"...","session_id":"...","skill":"...","success":true/false}`
   - Match start/end pairs by `session_id` + `skill`
   - Compute duration = end.ts - start.ts (in seconds)

2. **Read the registry** from `~/.claude/skills-management/data/registry.json` for skill metadata

3. **Calculate statistics:**

   **Per skill:**
   - Total invocations (all time, last 30 days, last 7 days)
   - Success rate (successful ends / total matched pairs)
   - Average duration
   - Incomplete calls (starts without matching ends)
   - Source breakdown (tool vs slash)

   **Overall:**
   - Total registered skills
   - Active skills (used in last 30 days)
   - Idle skills (not used in 30+ days)
   - Unused skills (registered but never invoked)
   - Total invocations in period

   **Trends:**
   - Compare last 7 days vs previous 7 days invocations
   - Show increasing/decreasing/stable for each skill

4. **Display results** as a formatted markdown report with tables:

   ```markdown
   ## Usage Summary (Last 30 Days)

   | Skill | Invocations | Success Rate | Avg Duration | Trend |
   |-------|------------|-------------|-------------|-------|
   | web-automation | 15 | 93% | 12.3s | ↑ |
   | ... | ... | ... | ... | ... |

   ## Idle Skills (30+ days unused)
   - example-skill (idle for 42 days)

   ## Overall
   - 5 registered, 3 active, 1 idle, 1 unused
   ```

## Notes
- If usage.jsonl does not exist or is empty, report "No usage data collected yet. Start using skills and run /scan to register them."
- If a skill_start has no matching skill_end, count as "incomplete" (not a failure)
- Sort the main table by invocation count (descending)
