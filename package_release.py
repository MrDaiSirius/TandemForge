"""Build the Windows preview ZIP from an explicit public source allowlist."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
VERSION = "v0.1.0-preview.1"
FILES = (
    "LICENSE", "README.md", "README.th.md", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "RELEASE.md", "VERIFICATION.md",
    "Setup TandemForge.cmd", "Run TandemForge.cmd", "Run Phone Access.cmd", "bootstrap.ps1",
    "engine.py", "runtime_guard.py", "model_guide.py", "personas.py", "preferences.py", "setup.py", "studio.py", "package_release.py",
    ".gitignore", ".github/FUNDING.yml.example", ".github/workflows/check.yml",
    "tests/test_runtime_guard.py",
    "tests/test_setup_downloads.py",
    "tests/check_bootstrap.ps1",
    "assets/ARTWORK.md", "workflows/edit.json", "workflows/flux.json",
    "dist/cover.webp", "dist/icon-180.png", "dist/icon-192.png", "dist/icon-512.png",
    "dist/index.html", "dist/locale.js", "dist/manifest.webmanifest", "dist/mark.svg",
    "dist/pairing.webp", "dist/settings.js", "dist/studio.css", "dist/studio.js", "dist/sw.js",
)


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"TandemForge-{VERSION}-Windows-x64.zip"
    temporary = destination.with_suffix(".zip.tmp")
    members = [f"TandemForge/{file}" for file in FILES]
    with ZipFile(temporary, "w") as archive:
        for file, member in zip(FILES, members, strict=True):
            path = ROOT / file
            if path.resolve() != path or not path.is_file():
                raise OSError(f"Missing or linked release file: {file}")
            archive.writestr(ZipInfo(member, (2026, 1, 1, 0, 0, 0)), path.read_bytes(), ZIP_DEFLATED)
    with ZipFile(temporary) as archive:
        if archive.namelist() != members or archive.testzip() is not None:
            raise OSError("Release ZIP verification failed.")
    temporary.replace(destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    print(build(parser.parse_args().output))
