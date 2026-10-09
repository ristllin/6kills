---
name: camera-shoot
description: Take photos with the cameras connected to this computer (USB webcams, built-in laptop cameras). Use whenever the user asks to take a photo, picture, snapshot, or selfie, says "shoot", "use the camera", "what does the camera see", or "look at X" for anything physical - the room, the desk, a whiteboard, hardware, an LED, a device screen - and for photo series or timelapses. On first use it discovers the cameras, asks the user a few setup questions, and saves the answers to its config.
---

# Camera shoot

Capture still photos from the cameras attached to this machine, **for you (the
agent) to look at**. The photos exist so you can see something physical and act on
it. They aren't a deliverable for the user to browse. The skill ships
with an **empty config**. On first use you discover what's connected, ask the user
how they want to use it, verify a test shot, and save everything to `config.json`.
Every later use reads the config and goes straight to the capture.

## Step 0: load the config

The config is `config.json` in this skill's directory (the folder that holds this
`SKILL.md`). A backup copy lives at `~/.config/camera-shoot/config.json`, because
plugin updates can replace the skill folder.

1. Read `config.json`.
2. If it has `"configured": false` but the backup exists and has
   `"configured": true`, copy the backup over `config.json` and use it.
3. If it's still unconfigured, or the user asks to reconfigure / change the default
   camera, run **First-time setup** below.
4. If it's configured but has no `vision.mode` (an older config), take a test shot
   and run setup steps 5 and 5b only, then save.
5. Otherwise go to **Taking a shot**. If a capture fails because the configured
   camera is missing, list devices again (see Discovery). Fall back to another
   configured camera only after telling the user, and offer to rerun setup.

Never guess a device name: use the exact `device_id` strings from the config or
from a fresh device listing.

## First-time setup

Work through these in order. Keep the user informed in one line per stage.

### 1. Discover the platform and capture tool

Detect the OS **first, on its own** (`uname -s`; on Windows, `$env:OS` or `ver`).
From then on run only that platform's commands: never probe Linux paths like
`/dev/video*` on macOS or Windows, or vice versa. Stray probes trigger needless
permission prompts. Then find a capture tool, in this order of preference:

| Platform | Preferred | Fallback | Check |
|---|---|---|---|
| macOS | `imagesnap` | `ffmpeg` (avfoundation) | `command -v imagesnap ffmpeg` |
| Linux | `fswebcam` | `ffmpeg` (v4l2) | `command -v fswebcam ffmpeg` |
| Windows | `ffmpeg` (dshow) | - | `where ffmpeg` |

If no tool is installed, tell the user which one to install (`brew install
imagesnap` on macOS, `sudo apt install fswebcam` or the distro equivalent on Linux,
`winget install ffmpeg` on Windows) and **ask before installing anything**.

Record the tool name and its absolute path (`command -v <tool>`).

### 2. Discover the cameras

List video devices:

- macOS, imagesnap: `imagesnap -l`
- macOS, ffmpeg: `ffmpeg -f avfoundation -list_devices true -i ""` (video devices
  are listed first, with an index)
- Linux: `v4l2-ctl --list-devices` if available, else `ls /dev/video*`. One USB
  camera often exposes two nodes; the lower-numbered one usually captures frames.
- Windows: `ffmpeg -list_devices true -f dshow -i dummy`

For each camera record the exact `device_id` the tool needs (copy names
character-for-character, including symbols like `®`), a short human `label`, and a
`kind`: `builtin`, `usb`, `virtual` (OBS, Continuity Camera, phone bridges), or
`unknown`. On macOS, `system_profiler SPCameraDataType` gives extra detail.

If no cameras are found, stop and tell the user. Suggest checking the cable or the
OS camera privacy settings.

### 3. Work out the capture method (camera permission)

Operating systems gate camera access per app. Try one direct capture to a temp file
with the default warm-up (see step 5 for the commands):

- **It works** → `"method": "direct"`.
- **Linux, permission denied** → the user needs to be in the `video` group
  (`sudo usermod -aG video $USER`, then log out and back in). Tell them; don't run
  `sudo` yourself.
- **macOS, "Camera access not granted", a hang, or an all-black frame on every try**
  → the process running you has no camera grant. This is common for agent hosts
  (desktop apps, IDE extensions, background shells). Build the bundled helper app,
  which owns its own grant:

  ```bash
  H="$HOME/Library/Application Support/camera-shoot"
  mkdir -p "$H"
  osacompile -o "$H/CameraShot.app" "<skill dir>/helper/camerashot.applescript"
  ```

  The helper must live outside the skill folder, because moving or rebuilding it
  makes macOS drop the grant. Then run one helper capture (see **Taking a shot**).
  The first run shows a macOS prompt, "CameraShot would like to access the camera".
  **Tell the user to click OK**: you can't approve it for them. If no prompt
  appears, have them enable CameraShot in System Settings → Privacy & Security →
  Camera (`open "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"`).
  Then set `"method": "helper"` and `"helper_app"` to the app's absolute path.

### 4. Ask the user

Ask these in one go. Use your harness's question tool if it has one; otherwise ask
in plain text and **stop until the user answers**. Offer the discovered cameras as
choices, with your recommendation first (an external USB camera is usually the one
pointed at something deliberately).

1. **Default camera**: which camera should I use when you don't name one?
2. **What will I be looking at with it?** Examples: a device screen or LEDs, the
   desk or a whiteboard, whether someone is at the desk, a 3D print in progress.
   This goes into `use_cases`. It tells you what to pay attention to when you
   inspect a shot later. Always ask it, even if the current request hints at an
   answer: one request ("photo of my desk") isn't the camera's ongoing purpose.

Don't ask where to save photos or whether to open them. The photos are for you,
not the user. Set `output_dir` yourself to a cache folder:
`~/.cache/camera-shoot` on macOS and Linux, `%LOCALAPPDATA%\camera-shoot` on Windows.

If the user names details about a camera (what it points at, where it's mounted),
add them to that camera's `notes`.

### 5. Verify with a test shot, and check that you can see it

Take one shot with the default camera into `output_dir`, using `warmup_seconds: 3`.
Then read the image file with your file-reading tool and decide honestly which case
you're in:

- **You see a picture** (your harness rendered it as an image): set
  `"vision": {"mode": "native"}`. Check the shot: if it's black or very dark, retry
  once with a 5-second warm-up. If 5 seconds fixes it, store `warmup_seconds: 5`. If
  the room is simply dark, say so and keep 3.
- **You get bytes, binary noise, base64 or an error instead of a picture**: your
  harness can't show you images from tools. Don't analyze the bytes or pixel
  statistics to infer the contents; that produces confident nonsense. Set up the
  vision fallback (step 5b).

Tell the user the result and the file path.

### 5b. Vision fallback (only when you can't see images)

The fallback is `helper/describe.py` in this skill's directory (Python 3, standard
library only). It sends one photo plus a question to a vision-capable model behind
any OpenAI-compatible chat-completions API and prints the answer. You use that text
as your eyes.

1. **Find candidate providers.** Check, without printing any key values:
   - your own harness's provider (it's usually already authorized, and the photo goes
     to the same company as the rest of the conversation). For example, Mistral Vibe
     reads `MISTRAL_API_KEY` and keeps it in the macOS Keychain under service
     `ai.mistral.vibe`, account `MISTRAL_API_KEY`.
   - API keys in the environment: `MISTRAL_API_KEY`, `OPENAI_API_KEY`,
     `OPENROUTER_API_KEY` (test with `[ -n "$NAME" ] && echo set`).
   - a local Ollama with a vision model (`ollama list`: look for llava, qwen2.5vl,
     gemma3, llama3.2-vision, minicpm-v). Local means photos never leave the machine.
2. **Ask the user** which to use, with your recommendation first. Mention that each
   photo becomes one API call (a fraction of a cent on hosted APIs) and is sent to
   that provider. Stop until they answer.
3. **Record it** in `config.json`:

   | Field | Mistral | OpenAI | Ollama (local) |
   |---|---|---|---|
   | `endpoint` | `https://api.mistral.ai/v1` | `https://api.openai.com/v1` | `http://localhost:11434/v1` |
   | `model` | `mistral-medium-latest` | `gpt-4o-mini` | the vision model's name |
   | `api_key_env` | `MISTRAL_API_KEY` | `OPENAI_API_KEY` | `null` |

   If the key isn't in the environment of the shell you run commands in, set
   `api_key_cmd` to a command that prints it, such as
   `security find-generic-password -s ai.mistral.vibe -a MISTRAL_API_KEY -w`
   on macOS. `describe.py` runs that command itself and keeps the key in memory.

   **The key value must never pass through you.** Don't run the key command
   yourself, and don't put the key in a command line, an `export`, a file, the
   config or your output. Any of those copies it into your session transcript and
   the process list, where it leaks. Hand `describe.py` only the env var's name or
   the command, and let it fetch the key.

   On macOS, reading another app's Keychain item makes macOS show an access dialog
   the first time. If `describe.py` exits 2 or the key command hangs, ask the user to
   run the key command once in their own terminal and click **Always Allow**, then
   stop. Don't hunt for another way to extract the key.
4. **Verify** it on the test shot:

   ```bash
   python3 "<skill dir>/helper/describe.py" --image /abs/test.jpg \
     --prompt "Describe this photo. Is it well exposed or too dark?" \
     --endpoint "<endpoint>" --model "<model>" \
     --api-key-env "<api_key_env>" --api-key-cmd "<api_key_cmd>"
   ```

   Leave out `--api-key-env`/`--api-key-cmd` when they're `null`. Exit code 2 means
   no key was found and 3 means an API error (the message says which). Fix it, or
   pick another provider with the user. Once it answers sensibly, apply the
   dark-frame check from step 5 using that answer.

### 6. Save the config

Write `config.json` with everything you learned, `"configured": true`, and
`configured_at` as an ISO timestamp. Then copy it to
`~/.config/camera-shoot/config.json` (create the folder). Example of a finished
config:

```json
{
  "configured": true,
  "configured_at": "2026-01-15T10:30:00Z",
  "platform": "macos",
  "capture": {
    "tool": "imagesnap",
    "tool_path": "/opt/homebrew/bin/imagesnap",
    "method": "helper",
    "helper_app": "/Users/me/Library/Application Support/camera-shoot/CameraShot.app"
  },
  "cameras": [
    {"device_id": "Logitech C920", "label": "desk webcam", "kind": "usb", "notes": "points at the test bench"},
    {"device_id": "FaceTime HD Camera", "label": "laptop camera", "kind": "builtin", "notes": ""}
  ],
  "default_camera": "Logitech C920",
  "warmup_seconds": 3,
  "output_dir": "/Users/me/.cache/camera-shoot",
  "use_cases": ["check the dev board's screen and LEDs"],
  "vision": {"mode": "native"},
  "notes": ""
}
```

With the fallback, `vision` looks like this instead:

```json
"vision": {
  "mode": "api",
  "endpoint": "https://api.mistral.ai/v1",
  "model": "mistral-medium-latest",
  "api_key_env": "MISTRAL_API_KEY",
  "api_key_cmd": "security find-generic-password -s ai.mistral.vibe -a MISTRAL_API_KEY -w"
}
```

## Taking a shot

Use `default_camera` unless the user names another camera (match their words
against each camera's `label`, `notes` and `device_id`). Name files
`shot-YYYYMMDD-HHMMSS.jpg` in `output_dir` (create it if missing). Use another path
only if the user explicitly asks for the photo to be kept somewhere. Always use absolute paths, and avoid spaces in output paths.

Capture commands (`W` = `warmup_seconds`, `DEV` = the camera's `device_id`):

- **imagesnap**: `imagesnap -d "DEV" -w W /abs/out.jpg`
- **ffmpeg, macOS**: `ffmpeg -loglevel error -f avfoundation -framerate 30 -i "DEV" -ss W -frames:v 1 -y /abs/out.jpg`
  (a numeric index works as `DEV` too)
- **fswebcam**: `fswebcam -d DEV -S $((W*15)) --no-banner -r 1280x720 /abs/out.jpg`
  (`-S` skips frames to warm up)
- **ffmpeg, Linux**: `ffmpeg -loglevel error -f v4l2 -i DEV -ss W -frames:v 1 -y /abs/out.jpg`
- **ffmpeg, Windows**: `ffmpeg -loglevel error -f dshow -i video="DEV" -ss W -frames:v 1 -y C:\abs\out.jpg`

With `"method": "direct"`, run the command as is.

With `"method": "helper"` (macOS), write the command line to the `args` file next to
the helper app and run the app. It runs that one command (it accepts only
`imagesnap` or `ffmpeg` commands with no shell metacharacters) and writes output
to `out.log`:

```bash
H="$(dirname "<helper_app>")"
printf '%s' 'imagesnap -d "DEV" -w W /abs/out.jpg' > "$H/args"
open -W "<helper_app>" && cat "$H/out.log"
```

The helper is shared by every agent on the machine, so don't run two captures at
the same time.

Warm-up matters: USB webcams need a few seconds to settle exposure and white
balance. Without it, frames come out black or badly underexposed.

## After capturing

1. Confirm the file exists and isn't tiny (`ls -l`). A normal 720p+ JPEG is
   usually 50 KB or more. A file of a few KB is almost always a failed or black frame.
2. **Look at the photo.**
   - `vision.mode` is `native`: read the image file with your file-reading tool.
   - `vision.mode` is `api`: run `helper/describe.py` (see step 5b) with a `--prompt`
     built from the user's request and the configured `use_cases`. Ask for exactly
     what you need, such as "What text is on the small screen? Which LEDs are lit and
     in what colour?" Its answer is what you saw. Ask a follow-up question in a
     second call if the first answer leaves the request open.

   Keep any derived images (a brightened or cropped copy) in `output_dir`, not
   `/tmp`.

   Check the shot isn't black or blurry. If it is, retake it with a longer warm-up
   or tell the user what's wrong (lights off, lens covered). Then use what you saw
   to answer the request, paying attention to `use_cases`.
3. **Never guess.** Describe only what you actually saw, natively or through
   `describe.py`. If reading the file gives you bytes instead of a picture, don't
   infer the contents from bytes, file size or pixel statistics. Switch to the
   fallback (rerun steps 5 and 5b) and tell the user.
4. Never open the photo in an image viewer or send it to the user unless they ask.

## Photographing screens and LEDs

Read this before drawing any conclusion from a photo of a lit display.

- **Backlit screens clip the webcam.** At normal brightness a lit screen photographs
  as near-white whatever it shows; a coloured halo around a white patch means
  clipping, not a wrong colour. Before judging colours, lower the screen's brightness
  (on a dev board 3-10 % backlight works well) and check the screen region isn't
  clipped (channel means near 255).
- **A webcam is not a colorimeter.** Auto exposure and white balance adapt to the
  room, so tints, gamma and exact hues in a photo say little about the screen. Use
  photos to judge what is shown, where, orientation, colour order and obvious
  defects. Never tune a display's colours from webcam photos.
- **Framing can change between sessions.** Re-locate the subject each time (a photo
  with the screen dark minus one with it lit isolates the screen).

## Photo series / timelapse

Loop single captures with a fresh timestamped filename each time. Don't use a tool's
own continuous mode (`imagesnap -t`, ffmpeg without `-frames:v`) through the helper:
nothing can stop it. Each helper capture adds about 2 seconds of launch overhead, so
intervals under about 5 seconds aren't realistic that way. Ask before starting a
series longer than a few minutes or more than about 50 frames.

## Troubleshooting

- **Helper `out.log` says "Camera access not granted"**: the helper lost its grant.
  This happens if it was rebuilt or moved. Run it once with the user present so they
  can click OK, or have them re-enable CameraShot in Privacy & Security → Camera.
- **Helper exits instantly with no log**: the `args` file is missing. Rewrite it
  and rerun.
- **Helper log says "refused"**: the command didn't start with `imagesnap`/`ffmpeg`,
  or contained `; & | $ ( ) < >` or a backtick. Rewrite it as one plain command.
- **`"method": "direct"` worked before but now fails, hangs or gives black
  frames**: camera grants belong to the app that launched you (a terminal, a desktop
  app, a background job), so a method saved in one context can be wrong in another.
  Re-run step 3 in this context and use the helper. Don't improvise other capture
  paths such as driving a browser.
- **Device busy or capture hangs**: another app (video call, Photo Booth) holds the
  camera. Ask the user to close it.
- **Camera not listed**: unplug and replug it, then list devices again. If the
  device name changed, update the config (and the backup).
- **`describe.py` exits 2 (no key)**: the key's env var isn't set in the shell
  your commands run in, or the key command failed or timed out (on macOS, usually
  an unanswered Keychain dialog). Ask the user to fix it, as in step 5b. Never
  extract the key yourself.
- **`describe.py` exits 3**: read the message. HTTP 401 means a bad key, 404 a wrong
  endpoint or model name, 400 often a model without vision. A network error means
  the endpoint isn't reachable (is Ollama running?).
- **Reconfigure**: when the user asks, run First-time setup again. Show the current
  values as the defaults.
