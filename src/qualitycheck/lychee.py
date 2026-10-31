"""lychee: found on PATH, else a pinned release downloaded once (ADR 0002)."""

import hashlib
import io
import os
import platform
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from qualitycheck.gates import Finding

VERSION = "0.24.2"
RELEASES = "https://github.com/lycheeverse/lychee/releases/download"
# Release asset and its SHA-256, per (system, machine).
ASSETS = {
    ("Windows", "x86_64"): (
        "x86_64-pc-windows-msvc.zip",
        "32975d1493ee1a975d6bb41e4fb56fe419cb442ded628bb772ba2e614acfacad",
    ),
    ("Linux", "x86_64"): (
        "x86_64-unknown-linux-musl.tar.gz",
        "73657a111819a30c47c08352896796f23d64e4eb2b3ed39b6d32149241566fc5",
    ),
    ("Linux", "aarch64"): (
        "aarch64-unknown-linux-musl.tar.gz",
        "5d0b0e3aeab240f41920c633a6eaf97599be6eedda034b36e858ede7dba5e535",
    ),
    ("Darwin", "aarch64"): (
        "aarch64-apple-darwin.tar.gz",
        "c9d3740ea2d891854d37116c9fba840f37b6e7c89d330e7db84ac333631c4977",
    ),
    ("Darwin", "x86_64"): (
        "x86_64-apple-darwin.tar.gz",
        "887503a9cff667d322b8d0892b40bf49976eb9507af8483220a3706cdad55978",
    ),
}
MACHINES = {
    "amd64": "x86_64",
    "x86_64": "x86_64",
    "arm64": "aarch64",
    "aarch64": "aarch64",
}
TIMEOUT = 60
CLIENT_ERRORS = range(400, 500)
TOO_MANY_REQUESTS = 429


def asset(system: str, machine: str) -> tuple[str, str] | None:
    """Return the release asset and its hash for a platform, or None."""
    return ASSETS.get((system, MACHINES.get(machine.lower(), machine.lower())))


def cache_dir() -> Path:
    """Return where downloaded tools are kept."""
    if os.environ.get("QUALITYCHECK_CACHE"):
        return Path(os.environ["QUALITYCHECK_CACHE"])
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME")
    return (
        Path(base) / "qualitycheck" if base else Path.home() / ".cache" / "qualitycheck"
    )


def _extract(archive: bytes, name: str, target: Path) -> None:
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            member = next(m for m in zipped.namelist() if Path(m).name == "lychee.exe")
            target.write_bytes(zipped.read(member))
        return
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tarred:
        member = next(m for m in tarred.getmembers() if Path(m.name).name == "lychee")
        target.write_bytes(tarred.extractfile(member).read())
    target.chmod(target.stat().st_mode | stat.S_IXUSR)


def _download(target: Path) -> Path | None:
    found = asset(platform.system(), platform.machine())
    if found is None:
        return None
    name, digest = found
    url = f"{RELEASES}/lychee-v{VERSION}/lychee-{name}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:  # nosec B310 - fixed https URL
            archive = response.read()
    except OSError:
        return None
    if hashlib.sha256(archive).hexdigest() != digest:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    _extract(archive, name, target)
    return target


def binary() -> Path | None:
    """Return lychee: on PATH, else cached, else downloaded; None if unavailable."""
    on_path = shutil.which("lychee")
    if on_path:
        return Path(on_path)
    suffix = ".exe" if platform.system() == "Windows" else ""
    target = cache_dir() / f"lychee-{VERSION}" / f"lychee{suffix}"
    return target if target.exists() else _download(target)


def _broken(entry: dict) -> bool:
    status = entry.get("status", {})
    code = status.get("code")
    if code is not None:
        return code in CLIENT_ERRORS and code != TOO_MANY_REQUESTS
    return status.get("text", "").startswith("File not found")


def broken_and_unchecked(report: dict) -> tuple[list[Finding], int]:
    """Split lychee's JSON report into broken links and links left unchecked."""
    broken, unchecked = [], 0
    for path, entries in report.get("error_map", {}).items():
        for entry in entries:
            if _broken(entry):
                line = entry.get("span", {}).get("line", 0)
                code = str(entry["status"].get("code", "file"))
                broken.append(Finding(path, line, code, entry["url"]))
            else:
                unchecked += 1
    unchecked += sum(len(entries) for entries in report.get("timeout_map", {}).values())
    return broken, unchecked
