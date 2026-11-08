# Preparing the first GitHub preview

Version `v0.1.0-preview.1` is a Windows x64 source preview with a single selectable setup. The downloadable ZIP contains the app, setup scripts, starter workflows and guides.

**Not published.** Review [VERIFICATION.md](VERIFICATION.md) before making a release decision. A simulated missing-Python test and a mobile viewport are not substitutes for a fresh Windows machine and real phone browsers. The maintainer must decide when to create the repository, publish the pre-release and activate Sponsors.

The source ZIP now includes the build script, Git ignore rules, CI workflow and local checks. Setup-managed AMD generation and editing passed on the documented 16 GB-class GPU; NVIDIA, Intel and lower-memory hardware remain unverified. The bundled edit workflow currently outputs 768 × 1024.

## Build the release files

Run this from the TandemForge source directory on Windows with Python 3.13 or newer.

```powershell
python package_release.py
```

The build creates `release/TandemForge-v0.1.0-preview.1-Windows-x64.zip` and its `.zip.sha256` file. The ZIP uses an explicit public-file list. Check the archive before uploading. The installer downloads models and runtimes from the links in [Third-party notices](THIRD_PARTY_NOTICES.md).

## Prepare the GitHub repository

1. Create the repository under the maintainer's GitHub account. Use **TandemForge** as the project name and add a description such as “A beginner-friendly Windows workspace for running local AI on your PC and using it privately from your phone.”
2. Commit the TandemForge source directory as the repository root, including `.github`, the license and both README files. Exclude machine data, access codes, session keys, outputs and downloads.
3. Review the tested configurations in [VERIFICATION.md](VERIFICATION.md) and complete the remaining checks below. Create a GitHub pre-release tagged `v0.1.0-preview.1` and attach the Windows ZIP and SHA-256 file. Use [CHANGELOG.md](CHANGELOG.md) as the release notes.
4. Enable the optional Sponsor button after the maintainer's GitHub Sponsors account is approved. Copy `.github/FUNDING.yml.example` to `.github/FUNDING.yml` and add the actual account name. The guides are the project's support channel.

## Remaining checks before broader release

- Extract the ZIP on a clean Windows 11 x64 profile. Start Setup without Python, add the CPU runtime and Qwen 2B, and send the first chat.
- Verify the chat tier on a physical 8 GB RAM PC.
- Generate and edit an Image Lab draft on each additional GPU family you plan to advertise. AMD passed on the measured 15.8 GiB VRAM machine. NVIDIA, Intel and lower-VRAM systems are still untested.
- Verify both Android and iPhone through the maintainer's test tailnet. Basic login and chat passed on one physical phone. Check a job in progress, OS background suspension and adding the app to the home screen on each platform.
