# LinkedIn Triage - Complete Setup Guide

Auto-triage your unread **LinkedIn DMs** with Claude, safely sandboxed in a Docker
container. It reads your DMs through the **Beeper Desktop** app, categorizes each one,
sends the right reply from templates you control, and leaves anything personal or
strategic **unread** for you to handle.

This guide takes you from a **fresh computer** to a working, optionally-scheduled triage.

---

## How it works (30-second version)

```
  Beeper Desktop app  ──(local MCP @ 127.0.0.1:23373)──┐
  (your LinkedIn DMs)                                   │
                                                        ▼
  ./run.sh  ──►  Docker container  ──►  Claude Code (claude -p /linkedin-triage)
                 (throwaway, isolated)      │  reads your rules file
                                            │  reads unread chats via Beeper tools
                                            └► sends replies, leaves the rest unread
```

- The AI runs **inside a container** that can only see: the triage skill, your rules
  file, and the Beeper messaging tools. Bash, file writes, and web access are **denied**.
- The container reaches the Beeper app on your host via `host.docker.internal`.
- Auth to Beeper uses the **OAuth token Claude Code already obtained** on your host - the
  run script reads it at runtime, so it self-heals whenever you re-authenticate.

---

## Prerequisites checklist

1. A **container runtime** (OrbStack or Docker Desktop) - installed and running
2. **Beeper Desktop** - installed, signed in, LinkedIn connected, local API enabled
3. **Claude Code** - installed, with the `beeper` MCP server added and authenticated
4. **API access** - either an `ANTHROPIC_API_KEY`, or a shared Foundry/gateway proxy (Mode B below)

Detailed steps for each are below. Then jump to **"Install & run the triage"**.

---

## Install Docker (container runtime)

LinkedIn Triage runs inside a Docker container, so you need a **container runtime** installed and running before anything else. A container runtime is the background service that builds and runs containers.

### macOS (recommended: OrbStack)

On macOS we recommend **OrbStack** - it is lighter and faster than Docker Desktop and starts almost instantly. (Docker Desktop also works fine if you prefer it; see below.)

1. Install OrbStack with Homebrew:

   ```bash
   brew install --cask orbstack
   ```

   If you don't use Homebrew, download the installer from [orbstack.dev](https://orbstack.dev) and drag it to your Applications folder.

2. Launch OrbStack and wait a few seconds for it to become ready:

   ```bash
   open -a OrbStack
   ```

### macOS / Windows (alternative: Docker Desktop)

1. Download Docker Desktop from [docker.com](https://www.docker.com) and run the installer.
2. Launch Docker Desktop from your Applications (macOS) or Start menu (Windows).
3. Wait until the Docker whale icon in your menu bar / system tray reports that Docker is running.

### Linux

1. Install Docker Engine by following the official instructions for your distribution: [docs.docker.com/engine/install](https://docs.docker.com/engine/install).
2. Make sure the Docker daemon is running:

   ```bash
   sudo systemctl enable --now docker
   ```

3. Add your user to the `docker` group so you can run Docker without `sudo`, then log out and back in (or run `newgrp docker`) for it to take effect:

   ```bash
   sudo usermod -aG docker $USER
   ```

### Verify your installation

Run these two commands. The first prints details about your running daemon; the second downloads and runs a tiny test image:

```bash
docker info
docker run --rm hello-world
```

If `hello-world` prints a "Hello from Docker!" success message, your runtime is working.

> **Note:** If the `docker` command is found but you see a **socket error** (for example, `Cannot connect to the Docker daemon` or `docker.sock: no such file`), the runtime app itself isn't running. Start OrbStack (`open -a OrbStack`) or Docker Desktop, wait ~15-20 seconds, then run `docker info` again.

---

## Install the Beeper Desktop app

[Beeper](https://www.beeper.com) is a universal chat app that unifies your conversations - iMessage, WhatsApp, LinkedIn, and more - into a single inbox. LinkedIn Triage reads and replies to your LinkedIn DMs *through* Beeper, so you must install the **desktop** app (the mobile app alone is not enough).

1. Download the **Beeper Desktop** app from [beeper.com](https://www.beeper.com) and install it.
2. Open Beeper and sign in (or create an account).
3. Inside Beeper, **connect your LinkedIn account** so your LinkedIn DMs appear in the Beeper inbox. Follow Beeper's on-screen prompts to link LinkedIn.

### Enable the local MCP server

Beeper Desktop can expose a **local MCP (Model Context Protocol) server** at:

```
http://localhost:23373/v0/mcp
```

This is the endpoint that lets local AI tools (like Claude Code) read and send your messages. You need to enable it:

1. Open Beeper's **Settings**.
2. Look for a section labeled **"Desktop API"**, **"Developer"**, or **"MCP"**. The exact label varies by Beeper version.
3. Enable the local API / MCP server.

> **Keep Beeper running.** The triage container talks to Beeper over `localhost`, so the Beeper Desktop app must stay **open and running** the entire time the triage runs.

> **Security note:** This API is **local-only** - it is bound to `127.0.0.1` (your own machine) and is not reachable from the network. It also requires an auth token, which Claude Code obtains automatically via OAuth in the next section. You do not need to copy or paste any token by hand.

---

## Install Claude Code and connect Beeper

LinkedIn Triage is a Claude Code skill, so you need Claude Code installed and connected to Beeper's MCP server.

### 1. Install Node.js and Claude Code

Claude Code requires **Node.js 18 or newer**. Install it from [nodejs.org](https://nodejs.org) (or via a version manager like `nvm`), then confirm the version:

```bash
node --version
```

Install Claude Code globally with npm:

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Authenticate Claude Code

For interactive use of Claude Code you can log in with a subscription or an API key. For the
**triage container specifically**, the runner supports two API auth modes and auto-detects
which one to use (see "API access modes" just below):

- **Mode A - direct key (default):** Create a key at [console.anthropic.com](https://console.anthropic.com) and set it in your environment:

  ```bash
  export ANTHROPIC_API_KEY="your-key-here"
  ```

  (Add this line to your `~/.zshrc` or `~/.bashrc` to make it permanent.)

- **Mode B - shared Foundry / gateway proxy:** If your org runs an Anthropic-compatible proxy
  that injects the key server-side, point the runner at it instead of holding a key yourself.

For interactive `claude` you can also just run `claude` and log in with a Claude subscription.

#### API access modes (for the triage container)

The `run.sh` runner picks a mode automatically:

| Mode | Triggered when | Variables |
|------|----------------|-----------|
| **A - direct key** (default) | `ANTHROPIC_API_KEY` is set and no Foundry vars are | `ANTHROPIC_API_KEY` (required); `ANTHROPIC_BASE_URL`, `TRIAGE_MODEL` (optional) |
| **B - Foundry / proxy** | `CLAUDE_CODE_USE_FOUNDRY=1` **or** `ANTHROPIC_FOUNDRY_BASE_URL` is set | `ANTHROPIC_FOUNDRY_BASE_URL` (required); `ANTHROPIC_FOUNDRY_API_KEY`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL` (optional) |

Mode B example (values come from your shared setup):

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
export ANTHROPIC_FOUNDRY_BASE_URL="https://<your-proxy-host>/anthropic"
# ANTHROPIC_FOUNDRY_API_KEY can be a placeholder if the proxy injects the real key
export ANTHROPIC_FOUNDRY_API_KEY="injected-by-proxy"
```

In Mode B the runner resolves the proxy's hostname on your host and pins it into the
container's `/etc/hosts`, so private DNS (e.g. Tailscale MagicDNS) reaches it from inside Docker.

### 3. Add the Beeper MCP server

Add Beeper to Claude Code **without** a static auth header. This is critical: a hardcoded token disables the OAuth flow and will cause `401` errors later.

```bash
claude mcp add --transport http beeper http://localhost:23373/v0/mcp -s user
```

> Do **not** pass an `Authorization` header (for example, `--header "Authorization: Bearer ..."`). Let Claude Code handle auth via OAuth.

### 4. Authenticate with Beeper

With the Beeper Desktop app running:

1. Start Claude Code:

   ```bash
   claude
   ```

2. Run the `/mcp` command.
3. Select **beeper**.
4. Choose **Authenticate**.
5. Approve the request in the Beeper app / your browser.

This stores an **auto-refreshing OAuth token** in your OS keychain (on macOS) or in `~/.claude/.credentials.json` (on Linux). You won't need to repeat this unless you revoke access.

### 5. Verify the connection

```bash
claude mcp list
```

The `beeper` entry should show **✔ Connected**. If it does, Claude Code can talk to Beeper and you're ready to run the triage.

---

## Install & run the triage

1. Put the `linkedin-triage-portable` folder anywhere on your machine (see the **Package files** section below to recreate it from scratch).

2. Run the setup checker - it verifies every prerequisite and builds the container image:

   ```bash
   cd linkedin-triage-portable
   ./setup.sh
   ```

   Fix anything it flags, then re-run until all checks pass.

3. **Build your rules.** This is the most important step - the quality of the replies depends
   entirely on it. Two ways:
   - **Interactive (recommended):** from Claude Code run `/linkedin-triage-init`. It interviews
     you about the messages you get, how you want to answer each, your red lines, referral policy,
     what to leave unread (and just be notified about), your calls policy, model, and schedule,
     then writes `memory/linkedin_triage_rules.md` and `config.env` for you.
   - **By hand:** open `memory/linkedin_triage_rules.md` and replace every `{{PLACEHOLDER}}` (your
     name, company, careers URL, optional referral link), then edit the categories/templates and
     the "leave unread / notify-only triggers" to match how *you* want to respond.

4. Make sure your API auth is set (Mode A or Mode B above) and the Beeper app is running, then triage:

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...    # Mode A (direct key)
   # -- or -- Mode B (shared proxy):
   # export CLAUDE_CODE_USE_FOUNDRY=1 ANTHROPIC_FOUNDRY_BASE_URL=https://<proxy>/anthropic
   ./run.sh
   ```

   The replies are sent through Beeper; a summary prints at the end telling you which chats
   were handled and which were left unread for you.

---

## Schedule it (optional, macOS)

Run the triage automatically every day (e.g. 9:00 AM):

```bash
./schedule/update-schedule.sh 9 0
```

This installs a `launchd` job under `~/Library/LaunchAgents/`. Logs go to
`~/Library/Logs/linkedin-triage.log`. To change the time, re-run with a new hour/minute.
To remove it, the command prints the exact `launchctl unload ...` line.

> The scheduled run needs the Beeper Desktop app to be running at that time, and it captures
> whichever auth vars you have set (Mode A or Mode B) from the shell where you run
> `update-schedule.sh`.

**Linux:** add a `cron` entry pointing at `run.sh` with your auth vars exported.
**Windows:** use Task Scheduler to run `run.sh` via WSL/Git Bash.

---

## How the sandbox protects you

- The container's `settings.json` **allows only** the Beeper MCP tools and read access, and
  **denies** `Bash`, `Write`, `Edit`, `WebSearch`, and `WebFetch`.
- The container's home is a throwaway `/sandbox`; only four things are mounted in
  (read-only): the skill, your rules memory, the permissions file, and a generated
  `~/.claude.json` holding the Beeper connection.
- The Beeper token is written to a local `.claude.runtime.json` (git-ignored, `chmod 600`)
  only at run time and is never committed.
- Nothing from your real home directory, SSH keys, or other projects is visible to the AI.

---

## Package files

Recreate the package by making a folder `linkedin-triage-portable/` with these files. (If you
received the folder directly, you can skip this section.)

### `run.sh`
Reads your live Beeper token, generates the container's MCP config, and runs the triage in an
isolated container. Requires API auth in one of two modes (a direct `ANTHROPIC_API_KEY`, or a
Foundry/proxy setup). Detects Docker and gives clear errors if a prerequisite is missing.

### `Dockerfile`
```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates dnsutils \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g @anthropic-ai/claude-code
ENV HOME=/sandbox
WORKDIR /workspace
ENTRYPOINT ["claude"]
```

### `settings.json` (container permissions)
```json
{
  "permissions": {
    "allow": ["mcp__beeper__*", "Read(*)"],
    "deny": ["Bash(*)", "Write(*)", "Edit(*)", "WebSearch(*)", "WebFetch(*)"]
  }
}
```

### `SKILL.md`
The triage instructions (categorize → reply from templates → leave the rest unread → report).

### `memory/linkedin_triage_rules.md`
**The file you customize.** Your name/company/links, the categories (job seeker, vendor,
recruiter, networking, personal, ...), and the exact reply template for each.

> The full contents of `run.sh`, `setup.sh`, `SKILL.md`, and the rules template ship with the
> package. The two key gotchas they encode:
> 1. **MCP config must live in `~/.claude.json`**, not `settings.json` - Claude Code ignores
>    `mcpServers` in `settings.json`.
> 2. **Never hardcode a Beeper `Authorization` header** in Claude Code - it disables OAuth and
>    401s when the token rotates. The run script reads the live OAuth token instead.

---

## Troubleshooting

### "Server rejected the configured Authorization header (HTTP 401)" when connecting beeper

**Cause:** The MCP configuration contains a stale or hardcoded `Authorization: Bearer ...` token, which prevents the OAuth flow from running.

**Fix:** Remove and re-add the server **without** any header, then re-authenticate:

```bash
claude mcp remove beeper -s user
claude mcp add --transport http beeper http://localhost:23373/v0/mcp -s user
```

Then run `claude`, use `/mcp`, select **beeper**, and choose **Authenticate**.

### "failed to connect to the docker API ... docker.sock: no such file"

**Cause:** The Docker/OrbStack daemon isn't running.

**Fix:** Launch your container runtime and give it time to start:

```bash
open -a OrbStack   # or start Docker Desktop
```

Wait ~15-20 seconds, then confirm it's up:

```bash
docker info
```

### "The Beeper MCP server isn't connected" (inside the container)

**Cause:** Usually one of the following:

- The **Beeper Desktop app isn't running** - open it and leave it running.
- The **host hasn't authenticated** the Beeper MCP server - run `claude`, use `/mcp`, select **beeper**, and choose **Authenticate**.
- The **OAuth token couldn't be read** from the OS keychain (macOS) or `~/.claude/.credentials.json` (Linux) - re-authenticate via `/mcp`.

### Beeper tools work on the host but not in the container

**Cause:** The container reaches services on your machine via the special hostname `host.docker.internal`. OrbStack routes this to the host loopback automatically, so no extra setup is needed.

**Fix:** If you're using plain Docker Desktop and the container can't reach the Beeper port on `127.0.0.1`, make sure the container is started with:

```
--add-host=host.docker.internal:host-gateway
```

(The provided run script already includes this flag, so this only matters if you launch the container manually.)

### Empty or wrong replies

**Cause:** The triage rules file hasn't been customized, so the skill has no guidance on how to categorize or respond to your DMs.

**Fix:** Edit `memory/linkedin_triage_rules.md` to define your own categories and reply templates.
