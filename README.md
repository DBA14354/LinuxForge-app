# LinuxForge

### Important: This project was vibe-coded using tools like Cursor and GitHub Copilot. There may be some bugs; but the app was tested on Ubuntu 26.04 and worked completely well. Expecting new versions to be released with an .appimage and .deb file.

A small desktop app for installing software on Linux without using the terminal.

LinuxForge detects **APT**, **Snap**, and **Flatpak**, then lets you:

- install common apps (Chrome, VS Code, JetBrains Toolbox, Discord, Steam, and others)
- search those package sources
- install a `.deb` file you already downloaded

Installs that need administrator access open the normal system password prompt (`pkexec`).

## Run

To run, you can look for "run.py", right-click, and select "Run as a program". You will have to wait a bit and LinuxForge will open.

Or you can also:

```bash
python3 run.py
```
