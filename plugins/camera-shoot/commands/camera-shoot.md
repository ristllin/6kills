---
description: "Take a photo with a connected camera (first run discovers cameras and asks a few setup questions)"
argument-hint: "[what to shoot, which camera, or 'setup' to reconfigure]"
allowed-tools: ["Bash", "Read", "Write", "Edit"]
---

Run the **camera-shoot** skill.

Request = `$ARGUMENTS`. If it's empty, take one photo with the default camera. If it says
`setup` or `reconfigure`, rerun the skill's first-time setup, showing the current values as
the defaults.

Follow the skill exactly: load `config.json` first (restore it from the
`~/.config/camera-shoot/config.json` backup if needed). If it's unconfigured, run discovery
and the setup questions, and stop for the user's answers before saving. Then capture, verify
the file, and report the path.
