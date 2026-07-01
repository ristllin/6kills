# 6kills

A public collection of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) skills.

Skills are self-contained folders that teach Claude how to do a specific task. Each one lives in `skills/<name>/` with a `SKILL.md` at its root. When installed, Claude reads the `description` in the frontmatter to decide when a skill applies, then loads the full instructions on demand.

## Structure

```
skills/
  <skill-name>/
    SKILL.md        # required: frontmatter + instructions
    ...             # optional: scripts, templates, reference files
```

## Using these skills

Clone into your Claude Code skills directory, or add individual skills:

```bash
# personal (all projects)
git clone https://github.com/ristllin/6kills.git ~/.claude/skills/6kills

# or copy a single skill
cp -r 6kills/skills/<skill-name> ~/.claude/skills/
```

Restart Claude Code (or start a new session) to pick up newly added skills.

## Authoring a skill

Every `SKILL.md` starts with YAML frontmatter:

```markdown
---
name: my-skill
description: One or two sentences describing what the skill does and when Claude should use it. This is what Claude matches against, so be specific about the triggers.
---

# My Skill

Instructions for the task...
```

Keep the body focused and actionable. Put large references, scripts, or templates in sibling files and point to them from `SKILL.md` so they load only when needed.

## License

[MIT](LICENSE)
