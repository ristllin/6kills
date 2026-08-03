# 📥 linkedin-triage

Auto-triage your unread **LinkedIn DMs** with Claude, safely sandboxed in a throwaway Docker
container. It reads your DMs through the **Beeper Desktop** app, categorizes each one
(job seeker, vendor, recruiter, networking, personal, ...), sends the right reply from
templates *you* control, and leaves anything personal or strategic **unread** for you.

Exposes the `/linkedin-triage` command.

## Why it's safe

The AI runs inside a disposable Docker container that can **only** see the triage skill, your
rules file, and the Beeper messaging tools. `Bash`, file writes, and web access are denied.
Nothing else on your machine (SSH keys, other projects, your real home) is exposed. The Beeper
auth token is read from your host at run time, written to a git-ignored `chmod 600` file, and
never committed.

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install linkedin-triage@6kills
```

## One-time setup (fresh machine)

`/linkedin-triage` detects an unconfigured machine and points you here. You need:

1. **Docker/OrbStack** installed and running.
2. **Beeper Desktop** installed, signed in, **LinkedIn connected**, local API enabled.
3. **Claude Code** with the `beeper` MCP server added and authenticated via `/mcp`.
4. **API access** - either your own `ANTHROPIC_API_KEY`, or a shared Foundry/gateway proxy
   (see "API access" below).

Run the checker (it verifies all of the above and builds the image):

```bash
bash "$(dirname "$(command -v claude)")"   # not this - see note
bash <plugin>/sandbox/setup.sh
```

> The plugin files live under `${CLAUDE_PLUGIN_ROOT}` once installed. From Claude Code you can
> just run `/linkedin-triage`; it will run `setup.sh` for you and relay any missing steps.

Then **customize your reply templates** - this is the most important step:

```
<plugin>/sandbox/memory/linkedin_triage_rules.md
```

Replace every `{{PLACEHOLDER}}` (your name, company, careers URL, optional referral link) and
tune the categories/templates to how you actually want to respond.

**Full step-by-step from a clean machine:** [`sandbox/SETUP.md`](sandbox/SETUP.md).

## API access (two supported modes)

The runner auto-detects which to use:

| Mode | When | Vars |
|------|------|------|
| **Direct key** (default) | You have an Anthropic API key | `ANTHROPIC_API_KEY` (opt: `ANTHROPIC_BASE_URL`, `TRIAGE_MODEL`) |
| **Foundry / shared proxy** | `CLAUDE_CODE_USE_FOUNDRY=1` **or** `ANTHROPIC_FOUNDRY_BASE_URL` is set | `ANTHROPIC_FOUNDRY_BASE_URL` (opt: `ANTHROPIC_FOUNDRY_API_KEY`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`) |

The proxy mode also pins the proxy's hostname into the container's `/etc/hosts` (resolved on
the host) so private DNS such as Tailscale MagicDNS works from inside Docker.

## Run

```bash
# from Claude Code:
/linkedin-triage

# or directly:
bash <plugin>/sandbox/run.sh
```

## Schedule it (optional, macOS)

```bash
bash <plugin>/sandbox/schedule/update-schedule.sh 9 0   # run daily at 9:00 AM
```

Installs a per-user `launchd` job; logs to `~/Library/Logs/linkedin-triage.log`. It captures
whichever auth vars you have set at that moment. The removal command is printed when you run it.

## Files

| Path | Purpose |
|------|---------|
| `commands/linkedin-triage.md` | The `/linkedin-triage` slash command (launches the sandbox). |
| `sandbox/run.sh` | Runs the triage in a container (reads your Beeper token, mounts the skill). |
| `sandbox/setup.sh` | Verifies prerequisites and builds the image. |
| `sandbox/Dockerfile` | Minimal Node image with Claude Code installed. |
| `sandbox/settings.json` | Container permissions (only Beeper tools + Read; Bash/Write/Web denied). |
| `sandbox/SKILL.md` | The triage instructions run *inside* the container. |
| `sandbox/memory/linkedin_triage_rules.md` | **Your** categories + reply templates. Customize this. |
| `sandbox/schedule/update-schedule.sh` | Installs a macOS launchd job to run on a schedule. |
| `sandbox/SETUP.md` | Complete setup guide from a fresh machine. |
