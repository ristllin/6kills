FROM node:20-slim

# ca-certificates for HTTPS to the Anthropic API; dnsutils is handy for debugging.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

# Isolated home - nothing from the host lands here unless explicitly mounted.
ENV HOME=/sandbox
WORKDIR /workspace

ENTRYPOINT ["claude"]
