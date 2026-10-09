# LinuxForge

### Important: This project was vibe-coded using tools like Cursor and GitHub Copilot. There may be some bugs; but the app was tested on Ubuntu 26.04 and worked completely well.

A small desktop app for installing software on Linux without using the terminal.

LinuxForge detects **APT**, **Snap**, and **Flatpak**, then lets you:

- install common apps (Chrome, VS Code, JetBrains Toolbox, Discord, Steam, and others)
- search those package sources
- install a `.deb` file you already downloaded

Installs that need administrator access open the normal system password prompt (`pkexec`).

## Run

To run, you can look for "run.py", right-click, and select "Run as a program". You will have to wait a bit and LinuxForge will open.
Or:

```bash
python3 run.py
```

Needs Python 3.10+ and PyQt6 (`sudo apt install python3-pyqt6` on Ubuntu/Debian).

## Packages

Build both a Debian installer and an AppImage:

```bash
./build.sh
```

Or separately:

```bash
./packaging/build_deb.sh
./packaging/build_appimage.sh
```

Outputs land in `dist/`:

- **`linuxforge_1.0.0_all.deb`** — installer for Ubuntu/Debian. Install with:
  ```bash
  sudo apt install ./dist/linuxforge_1.0.0_all.deb
  ```
  After that, open **LinuxForge** from the app menu or run `linuxforge`.
- **`LinuxForge-1.0.0-x86_64.AppImage`** — portable app. Make it executable and run it:
  ```bash
  chmod +x dist/LinuxForge-1.0.0-x86_64.AppImage
  ./dist/LinuxForge-1.0.0-x86_64.AppImage
  ```

The `.deb` uses your system Python and PyQt6. The AppImage bundles Python and Qt, so it does not need those packages installed first.
