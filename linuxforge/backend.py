from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from linuxforge.catalog import CatalogApp, Source

LogFn = Callable[[str], None]

MANAGER_LABELS = {
    "apt": "APT (.deb)",
    "snap": "Snap",
    "flatpak": "Flatpak",
    "deb_url": "Official .deb",
    "toolbox": "Official installer",
}


@dataclass(frozen=True)
class ManagerStatus:
    apt: bool
    snap: bool
    flatpak: bool

    def available_names(self) -> list[str]:
        names: list[str] = []
        if self.apt:
            names.append("apt")
        if self.snap:
            names.append("snap")
        if self.flatpak:
            names.append("flatpak")
        return names

    def summary(self) -> str:
        found = self.available_names()
        if not found:
            return "No package managers found (apt, snap, or Flatpak)."
        return "Detected: " + ", ".join(found)


@dataclass(frozen=True)
class SearchHit:
    name: str
    manager: str
    description: str
    package: str
    extra_args: tuple[str, ...] = ()


def detect_managers() -> ManagerStatus:
    return ManagerStatus(
        apt=_has_cmd("apt-get") or _has_cmd("apt"),
        snap=_has_cmd("snap"),
        flatpak=_has_cmd("flatpak"),
    )


def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def pick_source(app: CatalogApp, status: ManagerStatus) -> Source | None:
    for source in app.sources:
        if source.manager == "apt" and status.apt:
            if _apt_package_known(source.package):
                return source
        elif source.manager == "snap" and status.snap:
            return source
        elif source.manager == "flatpak" and status.flatpak:
            return source
        elif source.manager in {"deb_url", "toolbox"}:
            return source
    for source in app.sources:
        if source.manager == "apt" and status.apt:
            return source
    return None


@lru_cache(maxsize=256)
def _apt_package_known(package: str) -> bool:
    try:
        result = subprocess.run(
            ["apt-cache", "show", package],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False


def clear_status_cache() -> None:
    _apt_package_known.cache_clear()
    _dpkg_installed.cache_clear()
    _snap_installed.cache_clear()
    _flatpak_installed.cache_clear()


def is_installed(app: CatalogApp, status: ManagerStatus) -> bool:
    for source in app.sources:
        if source.manager == "apt" and status.apt and _dpkg_installed(source.package):
            return True
        if source.manager == "snap" and status.snap and _snap_installed(source.package):
            return True
        if source.manager == "flatpak" and status.flatpak and _flatpak_installed(source.package):
            return True
        if source.manager == "toolbox" and _toolbox_installed():
            return True
        if source.manager == "deb_url":
            guessed = {
                "chrome": "google-chrome-stable",
                "vscode": "code",
                "discord": "discord",
                "zoom": "zoom",
            }.get(app.id)
            if guessed and status.apt and _dpkg_installed(guessed):
                return True
    return False


@lru_cache(maxsize=256)
def _dpkg_installed(package: str) -> bool:
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "install ok installed" in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


@lru_cache(maxsize=256)
def _snap_installed(package: str) -> bool:
    try:
        result = subprocess.run(
            ["snap", "list", package],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@lru_cache(maxsize=256)
def _flatpak_installed(app_id: str) -> bool:
    try:
        result = subprocess.run(
            ["flatpak", "info", app_id],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _toolbox_installed() -> bool:
    home = Path.home()
    candidates = [
        home / ".local/share/JetBrains/Toolbox/bin/jetbrains-toolbox",
        home / ".local/share/JetBrains/Toolbox/jetbrains-toolbox",
    ]
    return any(path.is_file() for path in candidates)


def install_source(source: Source, log: LogFn) -> int:
    if source.manager == "apt":
        return _run(
            ["apt-get", "install", "-y", source.package],
            log,
            privileged=True,
            env_extra={"DEBIAN_FRONTEND": "noninteractive"},
        )
    if source.manager == "snap":
        return _run(
            ["snap", "install", source.package, *source.extra_args],
            log,
            privileged=True,
        )
    if source.manager == "flatpak":
        return _install_flatpak(source.package, log)
    if source.manager == "deb_url":
        return install_remote_deb(source.package, log)
    if source.manager == "toolbox":
        return install_jetbrains_toolbox(log)
    log(f"Unknown install method: {source.manager}")
    return 1


def install_local_deb(path: str, log: LogFn) -> int:
    deb = Path(path).expanduser().resolve()
    if not deb.is_file() or deb.suffix.lower() != ".deb":
        log("Choose a valid .deb file.")
        return 1
    log(f"Installing {deb.name} with APT…")
    return _run(
        ["apt-get", "install", "-y", str(deb)],
        log,
        privileged=True,
        env_extra={"DEBIAN_FRONTEND": "noninteractive"},
    )


def install_remote_deb(url: str, log: LogFn) -> int:
    log("Downloading package…")
    try:
        local = _download(url, suffix=".deb", log=log)
    except OSError as exc:
        log(f"Download failed: {exc}")
        return 1
    try:
        return install_local_deb(str(local), log)
    finally:
        try:
            local.unlink(missing_ok=True)
        except OSError:
            pass


def install_jetbrains_toolbox(log: LogFn) -> int:
    log("Looking up the latest JetBrains Toolbox…")
    api = "https://data.services.jetbrains.com/products/releases?code=TBA&latest=true&type=release"
    try:
        with urllib.request.urlopen(api, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        url = payload["TBA"][0]["downloads"]["linux"]["link"]
    except (OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
        log(f"Could not find Toolbox download: {exc}")
        return 1

    log("Downloading JetBrains Toolbox…")
    try:
        archive = _download(url, suffix=".tar.gz", log=log)
    except OSError as exc:
        log(f"Download failed: {exc}")
        return 1

    dest = Path.home() / ".local" / "opt" / "jetbrains-toolbox"
    dest.mkdir(parents=True, exist_ok=True)
    log(f"Extracting to {dest}…")
    try:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(dest, filter="data")
    except (OSError, tarfile.TarError) as exc:
        log(f"Could not extract archive: {exc}")
        return 1
    finally:
        try:
            archive.unlink(missing_ok=True)
        except OSError:
            pass

    binary = None
    for path in dest.rglob("jetbrains-toolbox"):
        if path.is_file() and os.access(path, os.X_OK):
            binary = path
            break
    if binary is None:
        log("Toolbox was downloaded but the program file was not found.")
        return 1

    log("Starting JetBrains Toolbox for the first-time setup…")
    try:
        subprocess.Popen(
            [str(binary)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"Could not start Toolbox: {exc}")
        return 1
    log("Toolbox is running. Finish setup in its window if it appears.")
    return 0


def _install_flatpak(app_id: str, log: LogFn) -> int:
    _ensure_flathub(log)
    cmd = ["flatpak", "install", "-y", "flathub", app_id]
    code = _run(cmd, log, privileged=False)
    if code == 0:
        return 0
    log("Retrying Flatpak install with administrator access…")
    return _run(cmd, log, privileged=True)


def _ensure_flathub(log: LogFn) -> None:
    result = subprocess.run(
        ["flatpak", "remote-list"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode == 0 and "flathub" in result.stdout.lower():
        return
    log("Adding the Flathub store…")
    _run(
        [
            "flatpak",
            "remote-add",
            "--if-not-exists",
            "flathub",
            "https://flathub.org/repo/flathub.flatpakrepo",
        ],
        log,
        privileged=False,
    )


def search_packages(query: str, status: ManagerStatus, log: LogFn) -> list[SearchHit]:
    query = query.strip()
    if len(query) < 2:
        return []
    hits: list[SearchHit] = []
    if status.apt:
        hits.extend(_search_apt(query, log))
    if status.snap:
        hits.extend(_search_snap(query, log))
    if status.flatpak:
        hits.extend(_search_flatpak(query, log))
    return _rank_hits(hits, query)


def _search_apt(query: str, log: LogFn) -> list[SearchHit]:
    log(f"Searching APT for “{query}”…")
    result = subprocess.run(
        ["apt-cache", "search", query],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        log("APT search failed.")
        return []
    return _parse_apt_search(result.stdout)


def _parse_apt_search(output: str) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for line in output.splitlines():
        if " - " not in line:
            continue
        name, desc = line.split(" - ", 1)
        hits.append(
            SearchHit(
                name=name.strip(),
                manager="apt",
                description=desc.strip(),
                package=name.strip(),
            )
        )
        if len(hits) >= 200:
            break
    return hits


def _rank_hits(hits: list[SearchHit], query: str) -> list[SearchHit]:
    needle = query.strip().lower()

    def key(hit: SearchHit) -> tuple[int, int, str]:
        package = hit.package.lower()
        name = hit.name.lower()
        if package == needle or name == needle:
            rank = 0
        elif package.startswith(needle) or name.startswith(needle):
            rank = 1
        elif needle in package or needle in name:
            rank = 2
        else:
            rank = 3
        manager_order = {"apt": 0, "flatpak": 1, "snap": 2}.get(hit.manager, 9)
        return (rank, manager_order, package)

    return sorted(hits, key=key)[:40]


def _search_snap(query: str, log: LogFn) -> list[SearchHit]:
    log(f"Searching Snap for “{query}”…")
    result = subprocess.run(
        ["snap", "find", query],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    if result.returncode != 0:
        log("Snap search failed (the Snap store may be offline).")
        return []
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    hits: list[SearchHit] = []
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        extra: tuple[str, ...] = ()
        joined = line.lower()
        if "classic" in joined:
            extra = ("--classic",)
        desc = " ".join(parts[4:]) if len(parts) > 4 else ""
        hits.append(
            SearchHit(
                name=name,
                manager="snap",
                description=desc or "Snap package",
                package=name,
                extra_args=extra,
            )
        )
        if len(hits) >= 40:
            break
    return hits


def _search_flatpak(query: str, log: LogFn) -> list[SearchHit]:
    log(f"Searching Flatpak for “{query}”…")
    _ensure_flathub(log)
    result = subprocess.run(
        ["flatpak", "search", "--columns=application,name,description", query],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    if result.returncode != 0:
        log("Flatpak search failed.")
        return []
    hits: list[SearchHit] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("application"):
            continue
        parts = [part.strip() for part in stripped.split("\t") if part.strip()]
        if not parts:
            continue
        app_id = parts[0]
        name = parts[1] if len(parts) > 1 else app_id
        desc = parts[2] if len(parts) > 2 else ""
        hits.append(
            SearchHit(
                name=name,
                manager="flatpak",
                description=desc or app_id,
                package=app_id,
            )
        )
        if len(hits) >= 40:
            break
    return hits


def source_from_hit(hit: SearchHit) -> Source:
    return Source(manager=hit.manager, package=hit.package, extra_args=hit.extra_args)


def _download(url: str, suffix: str, log: LogFn) -> Path:
    request = urllib.request.Request(url, headers={"User-Agent": "LinuxForge/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp.close()
        except Exception:
            tmp.close()
            Path(tmp.name).unlink(missing_ok=True)
            raise
    path = Path(tmp.name)
    log(f"Saved download ({path.stat().st_size // 1024} KB).")
    return path


def _run(
    cmd: list[str],
    log: LogFn,
    privileged: bool,
    env_extra: dict[str, str] | None = None,
) -> int:
    full = (["pkexec"] + cmd) if privileged else cmd
    log("$ " + " ".join(full))
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        process = subprocess.Popen(
            full,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        log(f"Command not found: {full[0]}")
        return 127
    assert process.stdout is not None
    for line in process.stdout:
        text = line.rstrip()
        if text:
            log(text)
    return process.wait()
