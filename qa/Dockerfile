# Clean-room image for 6kills release QA: the three agent harnesses and nothing from the host.
FROM node:22-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv git curl ca-certificates chromium jq \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code @openai/codex

# Claude Code refuses bypassPermissions as root, so the harnesses run as an unprivileged user.
RUN useradd -m -s /bin/bash qa
USER qa
ENV PATH="/home/qa/.local/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && uv tool install mistral-vibe

WORKDIR /home/qa
ENTRYPOINT ["bash", "/qa/in-container.sh"]
