# Preview verification

This is an **unreleased Windows x64 preview**, not a hardware certification. Results below were collected on 8 November 2026 (Asia/Bangkok). Publishing remains the maintainer's decision.

## Measured environment

- Windows 11 Pro x64, build 26200; Python 3.14.
- 31.6 GiB system RAM; AMD Radeon RX 9060 XT with approximately 15.8 GiB dedicated VRAM.
- Existing local llama.cpp-compatible engine and ComfyUI, plus a separate Setup-managed CPU runtime and AMD ComfyUI profile.
- Models, databases, access codes, session keys and personal network identities are excluded from the release archive.

## Results

| Check | Result and limit |
| --- | --- |
| Thai conversation | Three consecutive requests in each app; the name and preferred color survived the conversation history. |
| JSON and reasoning | Both apps returned the requested JSON fields and solved the arithmetic test correctly. |
| Actions | Both apps proposed `status` without executing it, executed it after approval, and rejected a second approval of the same plan. |
| App image attachments and history | Both apps identified the red-left / blue-right fixture. Reply copying and cancelling/confirming removal of one exchange passed in Windows Chrome. Other test entries remained. Actions were also approved from both normal web interfaces, including an emulated mobile viewport. |
| Multiple workspaces | Patched isolated instances handed off a real 9B chat workload. The waiting instance asked the idle owner to unload its chat model before loading its own. |
| Installer entry point | Opened `Setup TandemForge.cmd` from the extracted preview on Windows with Python already installed. The final installer files opened the expected Setup window and closed normally. |
| Multiple models and rerun | Retained the existing Setup-managed 2B model, downloaded 4B and both matching projectors, and completed all three Image Lab model downloads. Verified all hashes and repeated Setup successfully, including a UI rerun. |
| Setup-managed CPU inference | 2B answered the Thai first-chat arithmetic probe correctly; 4B completed a four-point Thai response. Both matching projectors identified the red/blue fixture on CPU with a 2,048-token context. |
| CPU chat with a commit limit | On the 31.6 GiB PC, TandemForge and its CPU engine shared a 3 GiB Windows Job Object commit limit. Qwen 2B at 2,048 context answered a short prompt in about four seconds. Peak combined commit was 1.14 GiB. This measures the app and engine, while a physical 8 GB Windows system remains a separate check. |
| Queue and browser reload | A 4B CPU job completed after navigating away and reloading the page; the reply and model label reappeared in Dialogue without logging in again. This does not test a mobile operating system suspending its browser. |
| Setup-managed AMD Image Lab | The installed AMD portable runtime started from the app and generated a decoded 512 × 512 draft. Reusing it for an edit changed a yellow bowl to blue; the current edit workflow rendered 768 × 1024. Both outputs passed HTTP Range reads and full decoding. NVIDIA and Intel remain untested. |
| Interrupted transfer | A local HTTP server cut a transfer after 1 MiB. Setup kept the partial file, sent a Range request on retry, and verified the completed file. This is a controlled transfer test, not a claim about every upstream server. |
| Existing files and failed setup | A mismatched existing model was preserved; a failed selection did not overwrite existing connections. |
| Relocated model folder | Renamed an isolated folder containing hardlinks to the verified 2B model/projector; Setup reconnected it, discovery found both, and the existing runtime completed inference from the new path. No personal model folder was moved. Its arithmetic error is recorded below. |
| Bootstrap branches | Simulated absent Python/PATH, registry discovery after installation, Winget invocation and missing Winget. These checks do not replace a clean Windows installation. |
| Responsive layout | All six screens checked at 360, 390, 412 and 1365 pixels in Thai and English: 48 cases without horizontal page overflow. The phone sizes use desktop browser emulation. |
| Existing private HTTPS | The companion personal app's existing Tailscale Serve route passed certificate validation, login, authenticated API requests and Secure/HttpOnly cookie checks; a foreign Origin received HTTP 403. No tailnet settings changed. |
| TandemForge private HTTPS | A temporary Tailscale Serve route reached TandemForge on its normal port. TLS, login, authenticated API requests, Secure/HttpOnly cookies, unauthenticated HTTP 401 and foreign-Origin HTTP 403 all passed. The temporary route was closed and the previous Serve configuration was verified. The client for this check was the Windows PC. |
| Physical phone chat | In a separate trial, the maintainer opened TandemForge on a phone over Tailscale, signed in and sent a chat message. The app recorded a completed chat job. |

The runtime coordinator only covers updated TandemForge and Local AI Studio instances in the same Windows session. Other applications and manually started model servers still consume their own memory. Restart an existing instance after updating its source files.

History removal now uses an in-page dialog with distinct Cancel and Remove buttons. The embedded test browser stalled on the old native confirmation dialog; the revised flow was verified in Windows Chrome, including 360- and 390-pixel viewports, cancellation and Escape. A Chrome-extension file-upload restriction was worked around with the ordinary Windows file picker; extension permissions were not changed.

The compact 2B model is a way to try short chats, not a measured reasoning tier. In this run it answered `18 + 24` correctly in a Thai UI request but returned `48` to a minimal English request after the folder move. The incorrect answer was retained. Successful installation, file hashes and completed inference do not establish answer accuracy. The 4B Thai response was a functional language check, not a factual-accuracy benchmark.

## Gates that remain open

- A fresh Windows 11 x64 installation without Python: actual Winget installation, first launch and first chat.
- A real 8 GB RAM PC; the 8 GB specification remains an estimate, not the result of a CPU test on this 31.6 GiB PC.
- NVIDIA and Intel hardware, and lower-VRAM configurations. AMD image generation and editing passed on this 15.8 GiB VRAM device only.
- Separate coverage for both iPhone and Android, Add to Home Screen, and operating-system background suspension. The phone chat above covers one physical device.

## Repeatable source checks

```powershell
python -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/check_bootstrap.ps1
python package_release.py
```

The Windows GitHub Actions workflow also checks Python, JavaScript and PowerShell syntax. The ZIP is built from an explicit public-file allowlist and includes the source checks and an inactive Sponsors example. No repository or release is created by these commands.
