---
name: report
description: "Generate a comprehensive skills usage report with trends, insights, and actionable recommendations. Use for periodic skill portfolio reviews."
---

# Skills Report Generator

## What to do

1. **Read all data:**
   - `~/.claude/skills-management/data/registry.json`
   - `~/.claude/skills-management/data/usage.jsonl`

2. **Generate the report** with these sections:

### Section 1: Portfolio Overview
- Total registered skills (by status: active/missing/deprecated)
- Skills by source (local, project)
- New skills registered this period

### Section 2: Usage Summary (Last 30 Days)
- Total invocations
- Top 5 most-used skills with invocation count and success rate
- Bottom 5 least-used active skills
- Overall success rate
- Average invocation duration

### Section 3: Trends
- Usage this week vs last week (percentage change)
- Skills with increasing usage (↑)
- Skills with decreasing usage (↓)
- Newly used skills (first invocation this period)

### Section 4: Recommendations

**Deprecation candidates** (unused 60+ days):
- List skill name, last used date, description
- Suggest: "Consider running /maintain to deprecate"

**Merge candidates** (high overlap):
- List similar skill pairs
- Suggest: "Consider running /maintain to merge"

**Update candidates** (low success rate):
- Skills with < 70% success rate and 3+ invocations
- Suggest: "Review and update this skill's instructions"

**Gap analysis**:
- Are there common user tasks that no skill covers?
- Based on the user's skill portfolio, what capabilities are missing?

### Section 5: Action Items
- Numbered list of suggested actions
- Each with the command to run (e.g., "Run /maintain to address 2 deprecation candidates")

3. **Format** as markdown and display to the user

4. **Save** a copy to `~/.claude/skills-management/data/reports/report-YYYY-MM-DD.md`
   - Create the reports directory if it doesn't exist

5. **Offer periodic setup:**
   If the user seems to find the report useful, suggest:
   "Want me to set up a weekly report? I can schedule it to run automatically every week."

## Notes
- If no usage data exists, still show Section 1 (portfolio overview) and suggest running /scan first
- Be concise — the report should be scannable in under 30 seconds
- Focus on actionable insights, not raw numbers
