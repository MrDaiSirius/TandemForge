"""Interactive Windows setup for TandemForge and its optional local runtimes."""

import hashlib
import json
import msvcrt
import os
import platform
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlsplit

import model_guide

ROOT = Path(__file__).resolve().parent
GIB = model_guide.GIB
DATA = Path(os.getenv("TANDEMFORGE_DATA", str(Path(os.environ["LOCALAPPDATA"]) / "TandemForge"))).resolve()
MANAGED_PORT = 8218


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    size: int
    sha256: str


def release(repo, version, name, size, sha256):
    return Asset(name, f"https://github.com/{repo}/releases/download/{version}/{name}", size, sha256)


def hub(repo, revision, remote, size, sha256, name=None):
    return Asset(name or Path(remote).name, f"https://huggingface.co/{repo}/resolve/{revision}/{remote}", size, sha256)


LLAMA = {
    "Vulkan": release("ggml-org/llama.cpp", "b12207", "llama-b12207-bin-win-vulkan-x64.zip", 37844756,
                      "c8c84eff8b7eae83602d3cf2dd6defe16c47d1011b4a2514905c1817e3a909ca"),
    "CPU": release("ggml-org/llama.cpp", "b12207", "llama-b12207-bin-win-cpu-x64.zip", 24886130,
                   "24447c546dca02bc449c7369eba07608cf5b170a59042ef388712654356d0d4c"),
}
COMFY = {
    "AMD": release("Comfy-Org/ComfyUI", "v0.44.0", "ComfyUI_windows_portable_amd.7z", 1671700941,
                   "b9ff564ced02a9a9f5dd3b6a5228ee2f1da33303a4f34f5438b8b80428fedd28"),
    "Intel": release("Comfy-Org/ComfyUI", "v0.44.0", "ComfyUI_windows_portable_intel.7z", 1486960018,
                     "f6af50a466e14db785996429cae92370490e7026150ea2d46f022b77f859d57d"),
    "NVIDIA": release("Comfy-Org/ComfyUI", "v0.44.0", "ComfyUI_windows_portable_nvidia.7z", 2054382457,
                      "7170c2db49c182a81adcc051e80234f99dd891656fb200737f87797876348f96"),
    "NVIDIA 10 series": release("Comfy-Org/ComfyUI", "v0.44.0", "ComfyUI_windows_portable_nvidia_cu126.7z",
                                1945636677, "a26cf84f043b3d9fbf0d53296f57d7190482c339caf1b3b5cfda5149d454be9f"),
}
CHAT_HASHES = {
    "qwen-2b": ("aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223", "mmproj-F16.gguf",
                668227264, "7035e9cb8d7c6a9681d07eef9a364783e86ea4cd73faab2eabb4f43a101830c7"),
    "qwen-4b": ("00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4", "mmproj-F16.gguf",
                672423616, "cd88edcf8d031894960bb0c9c5b9b7e1fea6ebee02b9f7ce925a00d12891f864"),
    "qwen-9b": ("03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8", "mmproj-F16.gguf",
                918166080, "f70dc3509053962b0d0d3ee8a7eacebf5d60aa560cad78254ae8698516ae029f"),
    "gemma-12b": ("3712b9bd32cae83a22f67ee7a4466d8d7a4f21646ac8a07d19bf9418e8767a70",
                  "mmproj-gemma-4-12B-it-Q8_0.gguf", 158987648,
                  "6b1088334bda27d7f293dcf426c0efaf1f1f20b65415ea354b695dbed9a0d65d"),
}
FLUX = {
    "diffusion_models": hub("black-forest-labs/FLUX.2-klein-4b-fp8", "5b4408e59397a4a37ccb46afe426d8ed86379441",
                            "flux-2-klein-4b-fp8.safetensors", 4070624520,
                            "97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6"),
    "text_encoders": hub("Comfy-Org/Flux-2-Klein-4B", "5b3abca5c0dc1ecd4eaf3340868d09063fc1c965",
                         "split_files/text_encoders/qwen_3_4b.safetensors", 8044982048,
                         "6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a"),
    "vae": hub("Comfy-Org/Flux-2-Klein-4B", "5b3abca5c0dc1ecd4eaf3340868d09063fc1c965",
               "split_files/vae/flux2-vae.safetensors", 336211292,
               "868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3"),
}
KEEP = "Keep / Skip"
EXISTING = "Use existing"
CPU_COMFY = "CPU only"
PREFERENCES = DATA / "connections.json"


def get_connections():
    if not PREFERENCES.is_file():
        return {}
    existing = json.loads(PREFERENCES.read_text(encoding="utf-8-sig"))
    if not isinstance(existing, dict):
        raise ValueError("connections.json must contain an object.")
    return existing


def chat_assets(keys, with_projectors):
    for spec in model_guide.CATALOG:
        if spec["id"] not in keys:
            continue
        sha, projector, size, projector_sha = CHAT_HASHES[spec["id"]]
        yield hub(spec["repo"], spec["revision"], spec["file"], spec["size"], sha)
        if with_projectors:
            filename = Path(spec["file"]).with_suffix(".mmproj.gguf").name
            yield hub(spec["repo"], spec["revision"], projector, size, projector_sha, filename)


def local_origin(value):
    address = urlsplit(value.strip().rstrip("/"))
    if (address.scheme != "http" or address.hostname not in ("127.0.0.1", "localhost")
            or address.username or address.password or address.path or address.query or address.fragment):
        raise ValueError("Use a local ComfyUI URL such as http://127.0.0.1:8188.")
    if address.port is None or not 0 < address.port <= 65535:
        raise ValueError("Include the local ComfyUI port, for example :8188.")
    return address.geturl()


def matches(path, asset):
    if not path.is_file() or path.stat().st_size != asset.size:
        return False
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest() == asset.sha256


def download(asset, folder, notify):
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / asset.name
    notify(f"Checking / ตรวจไฟล์ · {asset.name}")
    if target.exists():
        if matches(target, asset):
            return target
        raise OSError(f"An existing file differs from the expected hash. Keep it or choose a different folder: {target}")
    part = target.with_name(target.name + ".tandemforge.part")
    if part.is_symlink() or part.is_junction():
        raise OSError(f"Unexpected link in the download folder: {part}")
    if part.is_file() and part.stat().st_size > asset.size:
        part.unlink()
    if not part.is_file() or part.stat().st_size != asset.size:
        with subprocess.Popen(
            ["curl.exe", "--fail", "--location", "--silent", "--show-error", "--retry", "2",
             "--connect-timeout", "25", "--speed-time", "120", "--speed-limit", "1024",
             "--continue-at", "-", "--output", str(part), asset.url],
            stderr=subprocess.PIPE, text=True, errors="replace", creationflags=subprocess.CREATE_NO_WINDOW,
        ) as process:
            while True:
                try:
                    _, errors = process.communicate(timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    done = part.stat().st_size if part.is_file() else 0
                    notify(f"Downloading / ดาวน์โหลด · {asset.name} · {done / GIB:.2f} / {asset.size / GIB:.2f} GiB")
            if process.returncode:
                raise OSError(f"Download paused for {asset.name}. Run Setup again to resume.\n{errors.strip()}")
    notify(f"Verifying SHA-256 / ตรวจ SHA-256 · {asset.name}")
    if not matches(part, asset):
        part.unlink(missing_ok=True)
        raise OSError(f"SHA-256 or size did not match for {asset.name}. Run Setup again to retry.")
    part.rename(target)
    return target


def runtime_path(root, asset):
    return root / "runtimes" / (Path(asset.name).stem + "-" + asset.sha256[:10])


def runtime(root, asset, find_entry, notify):
    target = runtime_path(root, asset)
    if target.exists():
        return find_entry(target)
    archive = download(asset, root / "downloads", notify)
    stage = target.with_name(target.name + ".extracting")
    if stage.is_symlink() or stage.is_junction():
        raise OSError(f"Unexpected link in the runtime folder: {stage}")
    stage.mkdir(parents=True, exist_ok=True)
    notify(f"Extracting / แตกไฟล์ · {asset.name}")
    subprocess.run(["tar.exe", "-xf", str(archive), "-C", str(stage)], check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    find_entry(stage)
    stage.rename(target)
    archive.unlink()
    return find_entry(target)


def llama_entry(folder):
    found = list(folder.rglob("llama-server.exe"))
    if len(found) != 1:
        raise OSError(f"Expected one llama-server.exe in {folder}")
    return found[0]


def comfy_entries(folder):
    for bundle in [folder, *folder.iterdir()]:
        python = bundle / "python_embeded" / "python.exe"
        main = bundle / "ComfyUI" / "main.py"
        if python.is_file() and main.is_file():
            return python, main
    raise OSError(f"Could not find the ComfyUI portable layout in {folder}")


def disk_budget(plan):
    budget = {}

    def reserve(folder, bytes_needed):
        drive = Path(folder.anchor)
        budget[drive] = budget.get(drive, 0) + bytes_needed

    def add_file(asset, folder):
        file = folder / asset.name
        if file.is_file() and file.stat().st_size == asset.size:
            return
        part = file.with_name(file.name + ".tandemforge.part")
        done = part.stat().st_size if part.is_file() and part.stat().st_size <= asset.size else 0
        reserve(folder, asset.size - done)

    for asset in plan["models"]:
        add_file(asset, plan["model_dir"])
    for asset, extra in ((plan["llama_asset"], GIB // 3), (plan["comfy_asset"], 9 * GIB)):
        if asset and not runtime_path(DATA, asset).is_dir():
            add_file(asset, DATA / "downloads")
            reserve(DATA, extra)
    if plan["image_pack"]:
        if plan["comfy_asset"]:
            root = runtime_path(DATA, plan["comfy_asset"])
            model_root = comfy_entries(root)[1].parent / "models" if root.is_dir() else root / "models"
        else:
            model_root = plan["comfy_models"]
        for subdir, asset in FLUX.items():
            add_file(asset, model_root / subdir)
    return {drive: required + GIB for drive, required in budget.items() if required}


def install(plan, notify):
    if plan["tailscale"] and not tailscale_installed() and not shutil.which("winget.exe"):
        raise OSError("Windows App Installer (winget) is needed to install Tailscale.")
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "setup.lock").open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        for drive, required in disk_budget(plan).items():
            if shutil.disk_usage(drive).free < required:
                raise OSError(f"Free at least {required / GIB:.1f} GiB on {drive} for this selection.")
        connections = get_connections()
        if plan["llama_asset"]:
            connections["llama_exe"] = str(runtime(DATA, plan["llama_asset"], llama_entry, notify))
        elif plan["llama_existing"]:
            connections["llama_exe"] = str(plan["llama_existing"])
        for asset in plan["models"]:
            download(asset, plan["model_dir"], notify)
        connections["model_dir"] = str(plan["model_dir"])
        if plan.get("starter"):
            connections.update(starter_model=plan["starter"]["chat_id"], starter_context=plan["starter"]["context"])
        if plan["llama_asset"]:
            connections["starter_cpu"] = plan["llama_asset"] == LLAMA["CPU"]
        comfy_models = plan["comfy_models"]
        if plan["comfy_asset"]:
            python, main = runtime(DATA, plan["comfy_asset"], comfy_entries, notify)
            connections.update(comfy_python=str(python), comfy_main=str(main), comfy_cpu=plan["cpu_comfy"],
                               comfy_url=f"http://127.0.0.1:{MANAGED_PORT}")
            comfy_models = main.parent / "models"
        elif plan["comfy_url"]:
            for key in ("comfy_python", "comfy_main", "comfy_cpu"):
                connections.pop(key, None)
            connections["comfy_url"] = plan["comfy_url"]
        if plan["image_pack"]:
            for subdir, asset in FLUX.items():
                download(asset, comfy_models / subdir, notify)
        if plan["tailscale"] and not tailscale_installed():
            notify("Installing Tailscale / กำลังติดตั้ง Tailscale")
            subprocess.run(["winget.exe", "install", "--exact", "--id", "Tailscale.Tailscale", "--source", "winget",
                            "--silent", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements"],
                           check=True)
        temporary = PREFERENCES.with_suffix(".setup.tmp")
        temporary.write_text(json.dumps(connections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(PREFERENCES)


def tailscale_installed():
    return shutil.which("tailscale.exe") or (Path(os.environ["ProgramFiles"]) / "Tailscale" / "tailscale.exe").is_file()


def path_from(value):
    return Path(os.path.expandvars(value.strip())).expanduser().resolve()


class Wizard:
    def __init__(self, window):
        self.window = window
        self.events = queue.SimpleQueue()
        self.busy = False
        self.connections = get_connections()
        window.title("TandemForge Setup")
        window.geometry("805x670")
        window.minsize(690, 650)
        window.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="TandemForge Setup", font=("Segoe UI", 20, "bold")).grid(row=0, columnspan=3, sticky="w")
        ttk.Label(frame, text="Choose what to install · เลือกส่วนที่ต้องการติดตั้ง").grid(row=1, columnspan=3, sticky="w", pady=(0, 8))

        model_dir = os.getenv("TANDEMFORGE_MODELS") or self.connections.get("model_dir") or str(DATA / "models")
        specs = model_guide.guide(Path(model_dir))
        gpu = specs["gpu"]
        memory = f"RAM {specs['ram'] / GIB:.1f} GiB"
        if gpu:
            memory += f" · {gpu['name']} · {gpu['dedicated'] / GIB:.1f} GiB VRAM"
        ttk.Label(frame, text=memory, wraplength=700).grid(row=2, columnspan=3, sticky="w", pady=(0, 8))

        def choice(row, title, selected, choices):
            ttk.Label(frame, text=title).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            value = tk.StringVar(value=selected)
            ttk.Combobox(frame, textvariable=value, values=choices, state="readonly").grid(row=row, column=1, sticky="ew")
            return value

        def path_field(row, title, default, browser=None):
            ttk.Label(frame, text=title).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            value = tk.StringVar(value=default)
            ttk.Entry(frame, textvariable=value).grid(row=row, column=1, sticky="ew")
            if browser:
                def browse():
                    selected = browser(parent=window)
                    if selected:
                        value.set(selected)
                        if row == 4:
                            self.llama.set(EXISTING)
                ttk.Button(frame, text="Browse…", command=browse).grid(row=row, column=2, padx=(8, 0))
            return value

        existing_llama = os.getenv("TANDEMFORGE_LLAMA_EXE") or self.connections.get("llama_exe") or shutil.which("llama-server.exe")
        engine_default = KEEP if existing_llama or (DATA / "bin" / "llama-server.exe").is_file() else (
            "Vulkan" if gpu and gpu["dedicated"] >= 3.75 * GIB else "CPU")
        self.llama = choice(3, "Dialogue engine · เอนจินแชท", engine_default, (KEEP, EXISTING, *LLAMA))
        self.llama_path = path_field(4, "Existing llama-server.exe", existing_llama or "", filedialog.askopenfilename)
        self.model_dir = path_field(5, "Chat model folder · โฟลเดอร์โมเดล", model_dir, filedialog.askdirectory)
        has_models = any(not path.name.lower().startswith("mmproj") and ".mmproj." not in path.name.lower()
                         and "embed" not in path.name.lower() for path in Path(model_dir).glob("*.gguf"))
        row_models = ttk.LabelFrame(frame, text="Chat models · เลือกได้หลายโมเดล", padding=(9, 5))
        row_models.grid(row=6, columnspan=3, sticky="ew", pady=6)
        self.models = {}
        for index, spec in enumerate(model_guide.CATALOG):
            selected = not has_models and spec["id"] == specs["recommended"]
            var = tk.BooleanVar(value=selected)
            self.models[spec["id"]] = var
            suffix = " ★" if spec["id"] == specs["recommended"] else ""
            ttk.Checkbutton(row_models, variable=var, text=f"{spec['name']}  ({spec['size'] / GIB:.1f} GiB){suffix}"
                            ).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12))
        self.projectors = tk.BooleanVar(value=True)
        ttk.Checkbutton(row_models, text="Matching image projectors · ตัวอ่านภาพของโมเดลที่เลือก",
                        variable=self.projectors).grid(row=2, columnspan=2, sticky="w")

        self.comfy = choice(7, "ComfyUI for Image Lab", KEEP, (KEEP, EXISTING, *COMFY, CPU_COMFY))
        self.comfy_url = path_field(8, "Existing ComfyUI URL",
                                   os.getenv("TANDEMFORGE_COMFY_URL") or self.connections.get("comfy_url", "http://127.0.0.1:8188"))
        current_main = self.connections.get("comfy_main")
        self.comfy_models = path_field(9, "Existing ComfyUI models", str(Path(current_main).parent / "models") if current_main else "",
                                      filedialog.askdirectory)
        self.image_pack = tk.BooleanVar()
        self.comfy.trace_add("write", lambda *_: self.image_pack.set(self.comfy.get() not in (KEEP, EXISTING)))
        ttk.Checkbutton(frame, text=f"Image Lab model pack · ชุดสร้างและแก้ไขภาพ ({sum(a.size for a in FLUX.values()) / GIB:.1f} GiB)",
                        variable=self.image_pack).grid(row=10, columnspan=3, sticky="w")
        self.tailscale = tk.BooleanVar()
        tailscale = "Tailscale for phone access · ใช้จากมือถือ"
        if tailscale_installed():
            tailscale += " (installed)"
        ttk.Checkbutton(frame, text=tailscale, variable=self.tailscale).grid(row=11, columnspan=3, sticky="w")
        ttk.Label(frame, text=f"App data · ข้อมูลแอป  {DATA}", wraplength=720).grid(row=12, columnspan=3, sticky="w", pady=(10, 3))
        self.status = ttk.Label(frame, text="Review the choices, then click Install · เลือกเสร็จแล้วกดติดตั้ง", wraplength=720)
        self.status.grid(row=13, columnspan=3, sticky="w", pady=(0, 6))
        self.install_button = ttk.Button(frame, text="Install / ติดตั้ง", command=self.start)
        self.install_button.grid(row=14, column=0, sticky="w")
        self.launch_button = ttk.Button(frame, text="Open TandemForge", command=self.launch, state="disabled")
        self.launch_button.grid(row=14, column=1, sticky="e")
        self.window.after(200, self.update)

    def plan(self):
        if not self.model_dir.get().strip():
            raise ValueError("Choose a chat model folder.")
        selected = [key for key, var in self.models.items() if var.get()]
        model_dir = path_from(self.model_dir.get())
        guidance = model_guide.guide(model_dir)
        matching = [spec for spec in model_guide.CATALOG if spec["id"] in selected]
        starter = next((spec for spec in matching if spec["id"] == guidance["recommended"]),
                       matching[0] if matching else None)
        plan = {
            "llama_asset": LLAMA.get(self.llama.get()), "llama_existing": None,
            "models": tuple(chat_assets(selected, self.projectors.get())), "model_dir": model_dir,
            "starter": starter,
            "comfy_asset": COMFY.get(self.comfy.get()),
            "comfy_url": None, "comfy_models": None, "image_pack": self.image_pack.get(),
            "tailscale": self.tailscale.get(), "cpu_comfy": self.comfy.get() == CPU_COMFY,
        }
        if self.llama.get() == EXISTING:
            path = path_from(self.llama_path.get())
            if not path.is_file() or path.suffix.lower() != ".exe":
                raise ValueError("Choose the existing llama-server executable.")
            plan["llama_existing"] = path
        if plan["cpu_comfy"]:
            plan["comfy_asset"] = COMFY["NVIDIA 10 series"]
        if self.comfy.get() == EXISTING:
            plan["comfy_url"] = local_origin(self.comfy_url.get())
        if plan["image_pack"] and not plan["comfy_asset"]:
            if not self.comfy_models.get().strip() or not path_from(self.comfy_models.get()).is_dir():
                raise ValueError("Choose an existing ComfyUI models folder, or install a ComfyUI package here.")
            plan["comfy_models"] = path_from(self.comfy_models.get())
        return plan

    def start(self):
        try:
            plan = self.plan()
            space = disk_budget(plan)
        except (OSError, ValueError) as error:
            messagebox.showerror("TandemForge Setup", str(error), parent=self.window)
            return
        summary = "\n".join(f"{drive} · allow {required / GIB:.1f} GiB" for drive, required in space.items())
        if not messagebox.askokcancel("Install selected components?",
                                      (summary or "No new model or runtime downloads estimated.") +
                                      "\n\nSettings and your existing files are kept. Continue? / เริ่มติดตั้งหรือไม่",
                                      parent=self.window):
            return
        self.busy = True
        self.install_button.state(["disabled"])
        self.launch_button.state(["disabled"])

        def work():
            try:
                install(plan, lambda message: self.events.put(("status", message)))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.events.put(("error", str(error)))
            else:
                self.events.put(("done", "Setup complete / ติดตั้งเสร็จแล้ว · Restart TandemForge if it is open."))

        threading.Thread(target=work, daemon=True).start()

    def update(self):
        while not self.events.empty():
            kind, message = self.events.get_nowait()
            self.status.configure(text=message)
            if kind != "status":
                self.busy = False
                self.install_button.state(["!disabled"])
                if kind == "done":
                    self.launch_button.state(["!disabled"])
                else:
                    messagebox.showerror("TandemForge Setup", message, parent=self.window)
        self.window.after(200, self.update)

    def launch(self):
        os.startfile(ROOT / "Run TandemForge.cmd")

    def close(self):
        if self.busy:
            messagebox.showinfo("TandemForge Setup", "Setup is still running. Wait for the current installation.",
                                parent=self.window)
        else:
            self.window.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    try:
        if platform.machine().lower() not in ("amd64", "x86_64"):
            raise OSError("This preview setup requires 64-bit Windows on an x64 processor.")
        Wizard(window)
    except (OSError, ValueError) as error:
        messagebox.showerror("TandemForge Setup", str(error), parent=window)
        window.destroy()
    else:
        window.mainloop()
