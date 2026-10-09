from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    """One way to install an app."""

    manager: str
    package: str
    extra_args: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class CatalogApp:
    id: str
    name: str
    summary: str
    category: str
    sources: tuple[Source, ...] = field(default_factory=tuple)


CATALOG: tuple[CatalogApp, ...] = (
    CatalogApp(
        id="chrome",
        name="Google Chrome",
        summary="Google's web browser with sync and wide site support.",
        category="Browsers",
        sources=(
            Source("apt", "google-chrome-stable"),
            Source("flatpak", "com.google.Chrome"),
            Source(
                "deb_url",
                "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
                note="Official Google .deb",
            ),
        ),
    ),
    CatalogApp(
        id="firefox",
        name="Firefox",
        summary="Independent browser from Mozilla.",
        category="Browsers",
        sources=(
            Source("apt", "firefox"),
            Source("snap", "firefox"),
            Source("flatpak", "org.mozilla.firefox"),
        ),
    ),
    CatalogApp(
        id="chromium",
        name="Chromium",
        summary="Open-source browser that Chrome is based on.",
        category="Browsers",
        sources=(
            Source("apt", "chromium-browser"),
            Source("apt", "chromium"),
            Source("snap", "chromium"),
            Source("flatpak", "org.chromium.Chromium"),
        ),
    ),
    CatalogApp(
        id="brave",
        name="Brave",
        summary="Privacy-focused browser with built-in ad blocking.",
        category="Browsers",
        sources=(
            Source("snap", "brave"),
            Source("flatpak", "com.brave.Browser"),
            Source("apt", "brave-browser"),
        ),
    ),
    CatalogApp(
        id="vscode",
        name="Visual Studio Code",
        summary="Popular editor for code, Git, and extensions.",
        category="Development",
        sources=(
            Source("snap", "code", ("--classic",)),
            Source("apt", "code"),
            Source("flatpak", "com.visualstudio.code"),
            Source(
                "deb_url",
                "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64",
                note="Official Microsoft .deb",
            ),
        ),
    ),
    CatalogApp(
        id="jetbrains-toolbox",
        name="JetBrains Toolbox",
        summary="Install and update IntelliJ, PyCharm, WebStorm, and more.",
        category="Development",
        sources=(Source("toolbox", "jetbrains-toolbox"),),
    ),
    CatalogApp(
        id="intellij",
        name="IntelliJ IDEA Community",
        summary="Java and Kotlin IDE from JetBrains.",
        category="Development",
        sources=(
            Source("snap", "intellij-idea-community", ("--classic",)),
            Source("flatpak", "com.jetbrains.IntelliJ-IDEA-Community"),
        ),
    ),
    CatalogApp(
        id="pycharm",
        name="PyCharm Community",
        summary="Python IDE from JetBrains.",
        category="Development",
        sources=(
            Source("snap", "pycharm-community", ("--classic",)),
            Source("flatpak", "com.jetbrains.PyCharm-Community"),
        ),
    ),
    CatalogApp(
        id="docker",
        name="Docker",
        summary="Run applications in containers.",
        category="Development",
        sources=(
            Source("apt", "docker.io"),
            Source("snap", "docker"),
        ),
    ),
    CatalogApp(
        id="postman",
        name="Postman",
        summary="Build and test APIs.",
        category="Development",
        sources=(
            Source("snap", "postman"),
            Source("flatpak", "com.getpostman.Postman"),
        ),
    ),
    CatalogApp(
        id="discord",
        name="Discord",
        summary="Voice, video, and chat for communities and friends.",
        category="Communication",
        sources=(
            Source("snap", "discord"),
            Source("flatpak", "com.discordapp.Discord"),
            Source("apt", "discord"),
            Source(
                "deb_url",
                "https://discord.com/api/download?platform=linux&format=deb",
                note="Official Discord .deb",
            ),
        ),
    ),
    CatalogApp(
        id="slack",
        name="Slack",
        summary="Team chat and channels.",
        category="Communication",
        sources=(
            Source("snap", "slack"),
            Source("flatpak", "com.slack.Slack"),
            Source("apt", "slack-desktop"),
        ),
    ),
    CatalogApp(
        id="telegram",
        name="Telegram",
        summary="Fast messaging app.",
        category="Communication",
        sources=(
            Source("apt", "telegram-desktop"),
            Source("snap", "telegram-desktop"),
            Source("flatpak", "org.telegram.desktop"),
        ),
    ),
    CatalogApp(
        id="signal",
        name="Signal",
        summary="Private messenger.",
        category="Communication",
        sources=(
            Source("snap", "signal-desktop"),
            Source("flatpak", "org.signal.Signal"),
            Source("apt", "signal-desktop"),
        ),
    ),
    CatalogApp(
        id="zoom",
        name="Zoom",
        summary="Video meetings.",
        category="Communication",
        sources=(
            Source("snap", "zoom-client"),
            Source("flatpak", "us.zoom.Zoom"),
            Source(
                "deb_url",
                "https://zoom.us/client/latest/zoom_amd64.deb",
                note="Official Zoom .deb",
            ),
        ),
    ),
    CatalogApp(
        id="steam",
        name="Steam",
        summary="Games from Valve and thousands of other publishers.",
        category="Gaming",
        sources=(
            Source("apt", "steam-installer"),
            Source("apt", "steam"),
            Source("flatpak", "com.valvesoftware.Steam"),
            Source("snap", "steam"),
        ),
    ),
    CatalogApp(
        id="lutris",
        name="Lutris",
        summary="Play Windows and Linux games from one library.",
        category="Gaming",
        sources=(
            Source("apt", "lutris"),
            Source("flatpak", "net.lutris.Lutris"),
        ),
    ),
    CatalogApp(
        id="vlc",
        name="VLC",
        summary="Plays almost any video or audio file.",
        category="Media",
        sources=(
            Source("apt", "vlc"),
            Source("snap", "vlc"),
            Source("flatpak", "org.videolan.VLC"),
        ),
    ),
    CatalogApp(
        id="spotify",
        name="Spotify",
        summary="Music streaming.",
        category="Media",
        sources=(
            Source("snap", "spotify"),
            Source("flatpak", "com.spotify.Client"),
            Source("apt", "spotify-client"),
        ),
    ),
    CatalogApp(
        id="obs",
        name="OBS Studio",
        summary="Record and stream your screen.",
        category="Media",
        sources=(
            Source("apt", "obs-studio"),
            Source("flatpak", "com.obsproject.Studio"),
            Source("snap", "obs-studio"),
        ),
    ),
    CatalogApp(
        id="audacity",
        name="Audacity",
        summary="Record and edit audio.",
        category="Media",
        sources=(
            Source("apt", "audacity"),
            Source("flatpak", "org.audacityteam.Audacity"),
            Source("snap", "audacity"),
        ),
    ),
    CatalogApp(
        id="libreoffice",
        name="LibreOffice",
        summary="Writer, Calc, Impress, and other office tools.",
        category="Office",
        sources=(
            Source("apt", "libreoffice"),
            Source("flatpak", "org.libreoffice.LibreOffice"),
            Source("snap", "libreoffice"),
        ),
    ),
    CatalogApp(
        id="onlyoffice",
        name="ONLYOFFICE",
        summary="Office suite with strong Microsoft format support.",
        category="Office",
        sources=(
            Source("snap", "onlyoffice-desktopeditors"),
            Source("flatpak", "org.onlyoffice.desktopeditors"),
        ),
    ),
    CatalogApp(
        id="gimp",
        name="GIMP",
        summary="Photo and image editor.",
        category="Graphics",
        sources=(
            Source("apt", "gimp"),
            Source("flatpak", "org.gimp.GIMP"),
            Source("snap", "gimp"),
        ),
    ),
    CatalogApp(
        id="inkscape",
        name="Inkscape",
        summary="Vector drawing (logos, icons, diagrams).",
        category="Graphics",
        sources=(
            Source("apt", "inkscape"),
            Source("flatpak", "org.inkscape.Inkscape"),
            Source("snap", "inkscape"),
        ),
    ),
    CatalogApp(
        id="blender",
        name="Blender",
        summary="3D modeling, animation, and video editing.",
        category="Graphics",
        sources=(
            Source("apt", "blender"),
            Source("snap", "blender", ("--classic",)),
            Source("flatpak", "org.blender.Blender"),
        ),
    ),
    CatalogApp(
        id="krita",
        name="Krita",
        summary="Digital painting.",
        category="Graphics",
        sources=(
            Source("apt", "krita"),
            Source("flatpak", "org.kde.krita"),
            Source("snap", "krita"),
        ),
    ),
    CatalogApp(
        id="bitwarden",
        name="Bitwarden",
        summary="Password manager.",
        category="Utilities",
        sources=(
            Source("snap", "bitwarden"),
            Source("flatpak", "com.bitwarden.desktop"),
        ),
    ),
    CatalogApp(
        id="wine",
        name="Wine",
        summary="Run many Windows programs on Linux.",
        category="Utilities",
        sources=(
            Source("apt", "wine"),
            Source("flatpak", "org.winehq.Wine"),
        ),
    ),
)

CATEGORIES = (
    "All",
    "Browsers",
    "Development",
    "Communication",
    "Gaming",
    "Media",
    "Office",
    "Graphics",
    "Utilities",
)
