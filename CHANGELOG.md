# Changelog

## v0.1.0-preview.1

Windows x64 preview. See [tested configurations and outstanding checks](VERIFICATION.md).

- Coordinate model ownership between updated Studio instances so an idle loaded model yields memory to another workspace before its next model load.
- Add Windows process-handoff, crashed-owner recovery, interrupted-download, file-preservation and bootstrap-branch checks; include the build script, Git ignore rules, CI checks and inactive GitHub Sponsors example in the source ZIP.
- Verify three-turn Thai chat, JSON, reasoning and separately approved read-only Actions in both applications. Distinguish responsive desktop emulation and bootstrap simulations from physical-phone and fresh-Windows tests.
- Keep history-removal confirmation inside the page, with separate Cancel and Remove buttons, so embedded-browser native dialogs do not block the workspace.
- Keep the image-size hint synchronized with the selected draft or aspect preset.
- Verify Setup-managed 2B/4B CPU chat and projectors, a job surviving page reload, and AMD Image Lab generation/editing. Record the compact model's arithmetic limitation and the edit workflow's actual output size.
- Verify basic chat from one physical phone over Tailscale and CPU chat under a 3 GiB process-group commit budget.

- One selectable Windows setup for the chat engine, GGUF models, optional image projectors, ComfyUI, Image Lab models and Tailscale. Existing local runtimes can be reused.
- English and Thai interface and guides for a first local chat and private phone access.
- Hardware suggestions based on dedicated VRAM, system RAM and available model storage.
- Quick chat, reasoning, detailed instructions, image reading and JSON task modes where supported by installed models.
- Reply copying, visible model labels, projector checks, image drafts and adjustable image sizes.
- Local job activity and an approval step for the built-in Actions.
