# 📷 camera-shoot

**Give your agent eyes: it takes photos with the cameras on your machine and looks at them.**
It can check a device screen or LEDs, glance at the desk, read a whiteboard, or watch a print
with a timelapse. The photos are for the agent to look at, not a gallery for you.

The skill ships with an **empty config**. Nothing about your hardware is hard-coded. On
first use the agent:

1. Detects the OS and a capture tool (`imagesnap` or `ffmpeg` on macOS, `fswebcam` or
   `ffmpeg` on Linux, `ffmpeg` on Windows). It asks before installing anything.
2. Lists the connected cameras and records their exact device names.
3. Works out camera permissions. On macOS, many agent hosts (desktop apps, IDE extensions,
   background shells) can't get a camera grant themselves. In that case the agent builds a
   tiny helper app, `CameraShot.app`, which owns the grant. You click OK once.
4. Asks you two things: which camera is the default, and what it'll be looking at with it.
5. Takes a test shot and checks it can actually see it. If the harness can't show the
   model images from tools, it sets up a vision fallback: a small script that sends
   the photo to a vision model (your harness's own provider, another API, or a local
   Ollama, your choice) and returns a text description. It never guesses from raw bytes.
6. Tunes the warm-up if the frame comes out dark, and saves everything
   to `config.json`, with a backup at `~/.config/camera-shoot/config.json` that survives
   plugin updates. Photos go to a cache folder (`~/.cache/camera-shoot`).

After that, "take a photo of the bench" goes straight to the capture.

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install camera-shoot@6kills
```

The skill is a plain `SKILL.md` folder, so other harnesses that load skills can use it too.
For [Mistral Vibe](https://github.com/mistralai/mistral-vibe), copy
`skills/camera-shoot/` into `~/.vibe/skills/`.

## Usage

```
/camera-shoot                      # one photo with the default camera
/camera-shoot the laptop camera    # pick a camera by name or label
/camera-shoot setup                # rerun discovery and the setup questions
```

Or just ask in plain words: "take a picture of my desk", "what does the camera see?",
"take a photo every minute for 10 minutes".

## Files

```
skills/camera-shoot/
├── SKILL.md                       # discovery, setup, capture and troubleshooting steps
├── config.json                    # empty until first use; filled in by the agent
└── helper/
    ├── camerashot.applescript     # macOS camera-permission helper source (built on demand)
    └── describe.py                # vision fallback: photo + question -> any OpenAI-compatible vision API
```

## Notes

- **Seeing the photo:** the agent reads the image file itself and uses what it sees. In
  harnesses whose tools return only text (Mistral Vibe 2.26's `read_file`, for example),
  setup switches to the `describe.py` fallback. The API key is read from an env var or a
  command such as a Keychain lookup. It's never written to the config or printed.
- **The macOS helper** is built into `~/Library/Application Support/camera-shoot/`, outside
  the plugin folder, because macOS drops the camera grant when the app moves or is
  rebuilt. It runs only a single `imagesnap` or `ffmpeg` command with no shell
  metacharacters, read from the `args` file next to it.
- **Privacy:** photos are saved only in the local cache folder. When the agent looks at a
  photo, it goes to your model provider like any other file the agent reads.
