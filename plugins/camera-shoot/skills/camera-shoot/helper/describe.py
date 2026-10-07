#!/usr/bin/env python3
"""Vision fallback for the camera-shoot skill.

For agents whose harness can't show them images returned by tools: sends one photo
plus a question to a vision-capable model behind an OpenAI-compatible
chat-completions API (Mistral, OpenAI, OpenRouter, a local Ollama, ...) and prints
the model's text answer. Standard library only.

The API key comes from the environment variable named by --api-key-env, or, if that
is unset, from the stdout of --api-key-cmd (for example a keychain lookup). The key
is only ever sent in the Authorization header: it is never printed or logged.

Exit codes: 0 answer printed, 1 bad input, 2 no API key, 3 API/network error.
"""

import argparse
import base64
import json
import mimetypes
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request

MAX_IMAGE_BYTES = 10 * 1024 * 1024


def fail(code, msg):
    print(f"describe.py: {msg}", file=sys.stderr)
    sys.exit(code)


def get_key(env_name, key_cmd):
    if env_name and os.environ.get(env_name):
        return os.environ[env_name].strip()
    if key_cmd:
        try:
            out = subprocess.run(shlex.split(key_cmd), capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as exc:
            fail(2, f"api key command failed to run: {exc.__class__.__name__}")
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
        fail(2, f"api key command exited {out.returncode} with no key")
    if env_name is None and key_cmd is None:
        return None  # keyless endpoint, e.g. local Ollama
    fail(2, f"no API key: ${env_name or '(none)'} is unset and no working --api-key-cmd")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--image", required=True, help="absolute path to a JPEG/PNG/WebP/GIF")
    p.add_argument("--prompt", required=True, help="what to look for / answer about the photo")
    p.add_argument("--endpoint", required=True, help="base URL, e.g. https://api.mistral.ai/v1")
    p.add_argument("--model", required=True, help="vision-capable model id")
    p.add_argument("--api-key-env", help="env var holding the API key")
    p.add_argument("--api-key-cmd", help="command that prints the API key (used if the env var is unset)")
    p.add_argument("--max-tokens", type=int, default=600)
    p.add_argument("--timeout", type=int, default=90)
    a = p.parse_args()

    if not os.path.isfile(a.image):
        fail(1, f"no such image: {a.image}")
    size = os.path.getsize(a.image)
    if size == 0 or size > MAX_IMAGE_BYTES:
        fail(1, f"image size {size} bytes is out of range (1 B to 10 MB)")
    mime = mimetypes.guess_type(a.image)[0] or "image/jpeg"
    with open(a.image, "rb") as f:
        data_uri = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

    key = get_key(a.api_key_env, a.api_key_cmd)
    body = {
        "model": a.model,
        "max_tokens": a.max_tokens,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": a.prompt + "\n\nDescribe only what is actually visible. "
                 "If something asked about isn't visible or can't be read, say so."},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        }],
    }
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(a.endpoint.rstrip("/") + "/chat/completions",
                                 data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as resp:
            reply = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        fail(3, f"API returned HTTP {exc.code}: {detail}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(3, f"API request failed: {exc}")

    try:
        content = reply["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        fail(3, f"unexpected API response shape: {json.dumps(reply)[:300]}")
    if isinstance(content, list):  # some APIs return content chunks
        content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
    print(content.strip())


if __name__ == "__main__":
    main()
