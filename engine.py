import base64
import ctypes
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import personas
import preferences
from runtime_guard import RuntimeLease

ROOT = Path(__file__).resolve().parent
FOLDER = "TandemForge"
DATA = Path(os.getenv("TANDEMFORGE_DATA", str(Path(os.environ["LOCALAPPDATA"]) / FOLDER)))
OUTPUT = DATA / "outputs"
connections = DATA / "connections.json"
CONNECTIONS = json.loads(connections.read_text(encoding="utf-8-sig")) if connections.is_file() else {}
COMFY = (os.getenv("TANDEMFORGE_COMFY_URL") or CONNECTIONS.get("comfy_url") or "http://127.0.0.1:8188").rstrip("/")
address = urlsplit(COMFY)
if (address.scheme != "http" or address.hostname not in ("127.0.0.1", "localhost")
        or address.username or address.path or address.query or address.fragment):
    raise ValueError("TANDEMFORGE_COMFY_URL must be a local HTTP origin")
LU = Path(os.getenv("TANDEMFORGE_LLAMA_EXE") or CONNECTIONS.get("llama_exe")
          or shutil.which("llama-server.exe") or DATA / "bin" / "llama-server.exe")
MODELS = Path(os.getenv("TANDEMFORGE_MODELS") or CONNECTIONS.get("model_dir") or DATA / "models")
UPLOADS = DATA / "uploads"
WORK = DATA / "agent-workspace"
RECIPES = {
    "flux": {"label": "สร้างภาพ", "model": "FLUX.2 Klein", "kind": "image", "output": "9"},
    "edit": {"label": "แก้ไขภาพ", "model": "FLUX.2 Klein Edit", "kind": "image", "output": "9", "input": True},
}
IMAGE_SIZES = {"draft": (512, 512), "square": (768, 768), "portrait": (768, 1024), "landscape": (1024, 768)}
CHAT_MODELS = {
    "qwen9": ("Qwen 3.5 · 9B", "Qwen3.5-9B-abliterated.Q4_K_M"),
    "qwen2-stock": ("Qwen 3.5 · 2B", "Qwen3.5-2B-Q4_K_M"),
    "qwen4-stock": ("Qwen 3.5 · 4B", "Qwen3.5-4B-Q4_K_M"),
    "qwen9-stock": ("Qwen 3.5 · 9B Standard", "Qwen3.5-9B-Q4_K_M"),
    "gemma12": ("Gemma 4 · 12B IT", "gemma-4-12B-it-Q4_0"),
    "qwen35": ("Qwen 3.8 · 35B A3B", "Qwen3.8-35B-A3B-IQ2_M"),
    "orca27": ("Orca Qwen 3.8 · 27B", "orcarouter_Qwen3.8-27B-Uncensored-IQ2_M"),
    "qwen27": ("Qwen 3.8 · 27B", "Qwen3.8-27B-UD-Q3_K_XL"),
}


def chat_model_path(key):
    return MODELS / (CHAT_MODELS[key][1] + ".gguf")


def has_projector(key):
    return chat_model_path(key).with_suffix(".mmproj.gguf").is_file()


def discover_models():
    from hashlib import sha256
    for path in sorted(MODELS.glob("*.gguf")):
        name = path.stem
        lower = name.lower()
        if ".mmproj" in lower or lower.startswith("mmproj") or "embed" in lower:
            continue
        if name in (value[1] for value in CHAT_MODELS.values()):
            continue
        if "qwen3.5-9b" in lower and not (MODELS / (CHAT_MODELS["qwen9"][1] + ".gguf")).is_file():
            CHAT_MODELS["qwen9"] = ("Qwen 3.5 · 9B", name)
        else:
            CHAT_MODELS["local-" + sha256(name.encode()).hexdigest()[:12]] = (name, name)
    for key, (_, name) in list(CHAT_MODELS.items()):
        if not (MODELS / (name + ".gguf")).is_file():
            del CHAT_MODELS[key]


discover_models()
IMAGE_EXT = {".png", ".jpg", ".webp"}
MEDIA_EXT = IMAGE_EXT | {".mp4", ".flac", ".mp3", ".wav", ".ogg"}
AGENT_ACTIONS = {
    "status": "ตรวจสถานะ ComfyUI และคิว",
    "list": "ดูรายการไฟล์ในพื้นที่ Agent",
    "read": "อ่านไฟล์ในพื้นที่ Agent",
    "write": "บันทึกไฟล์ใหม่ในพื้นที่ Agent",
    "create": "ส่งงานสร้างสื่อเข้า ComfyUI",
}


def api(base, path, body=None, timeout=5):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(base + path, data, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            content = res.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read())
        except ValueError:
            raise RuntimeError(f"API HTTP {exc.code}") from None
        message = error.get("error", error)
        if isinstance(message, dict):
            message = message.get("message", message)
        nodes = error.get("node_errors")
        if nodes:
            message = f"{message} · {json.dumps(nodes, ensure_ascii=False)[:900]}"
        raise RuntimeError(str(message)[:1200]) from None


def comfy_queue():
    return api(COMFY, "/queue")


def comfy_status():
    try:
        q = comfy_queue()
        return {"online": True, "running": len(q["queue_running"]), "pending": len(q["queue_pending"])}
    except (OSError, RuntimeError):
        return {"online": False, "running": 0, "pending": 0}


def commit_percent():
    values = (ctypes.c_size_t * 14)()
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(values), ctypes.sizeof(values)):
        return None
    return round(values[1] / values[2] * 100, 1) if values[2] else None


def image_extension(raw):
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if raw.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    raise ValueError("รองรับภาพ PNG, JPEG และ WebP")


def uploaded(name):
    if not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|webp)", name or ""):
        raise ValueError("เลือกภาพใหม่แล้วลองอีกครั้ง")
    path = UPLOADS / name
    if not path.is_file():
        raise ValueError("ไม่พบภาพที่อัปโหลด")
    return path


def app_output(relative):
    base = (OUTPUT / FOLDER).resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or path.suffix.lower() not in MEDIA_EXT or not path.is_file():
        raise ValueError("ไม่พบไฟล์ผลงาน")
    return path


def source_image(payload):
    if payload.get("source"):
        path = app_output(payload["source"])
        if path.suffix.lower() not in IMAGE_EXT:
            raise ValueError("เลือกไฟล์ภาพเพื่อใช้เป็นต้นฉบับ")
        return path
    return uploaded(payload.get("image"))


def recipe_graph(recipe, payload, prefix, image_name=None):
    graph = json.loads((ROOT / "workflows" / (recipe + ".json")).read_text(encoding="utf-8-sig"))
    text = payload["text"]
    seed = secrets.randbits(48)
    graph[RECIPES[recipe]["output"]]["inputs"]["filename_prefix"] = prefix
    graph["4"]["inputs"]["text"] = text
    graph["10"]["inputs"]["noise_seed"] = seed
    if recipe == "edit":
        graph["14"]["inputs"]["image"] = image_name
    elif payload.get("size") in IMAGE_SIZES:
        width, height = IMAGE_SIZES[payload["size"]]
        graph["14"]["inputs"]["value"] = width
        graph["15"]["inputs"]["value"] = height
    return graph


def upload_comfy_image(image, job_id):
    boundary = "tandemforge-" + secrets.token_hex(16)
    name = job_id + image.suffix.lower()
    header = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
              "Content-Type: application/octet-stream\r\n\r\n").encode()
    tail = (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"subfolder\"\r\n\r\n{FOLDER}"
            f"\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(COMFY + "/upload/image", header + image.read_bytes() + tail,
                                 {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as response:
        item = json.load(response)
    return f"{FOLDER}/{item['name']}"


def save_comfy_image(item, job_id):
    name = item.get("filename", "")
    subfolder = item.get("subfolder", "").replace("\\", "/")
    if (item.get("type") != "output" or subfolder != f"{FOLDER}/{job_id}"
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or Path(name).suffix.lower() not in IMAGE_EXT):
        return None
    relative = f"{job_id}/{name}"
    dest = OUTPUT / FOLDER / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    query = urlencode({"filename": name, "subfolder": subfolder, "type": "output"})
    with urllib.request.urlopen(COMFY + "/view?" + query, timeout=30) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("The output image exceeded 64 MiB.")
    image_extension(data)
    temp = dest.with_suffix(".part")
    temp.write_bytes(data)
    temp.replace(dest)
    return {"path": relative, "name": name, "kind": "image"}


class Engines:
    def __init__(self):
        self.lease = RuntimeLease()
        self.llm = None
        self.comfy = None
        self.model_key = None
        self.llm_url = None
        self.idle_seconds = preferences.DEFAULTS["idle_seconds"]

    def stop_chat(self):
        if self.llm and self.llm.poll() is None:
            self.llm.terminate()
            try:
                self.llm.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.llm.kill()
                self.llm.wait()
        self.llm = self.model_key = self.llm_url = None
        self.lease.release()

    def yield_if_requested(self):
        if self.lease.requested():
            self.stop_chat()

    def start_chat(self, key, vision, config, agent, update):
        options = preferences.engine_options(config, vision, agent)
        signature = (key, vision, tuple(options))
        self.idle_seconds = config["idle_seconds"]
        status = comfy_status()
        if status["running"] or status["pending"]:
            self.stop_chat()
            raise RuntimeError("ComfyUI กำลังทำงานจากคิวอื่น รอให้คิวว่างแล้วลองใหม่")
        if self.model_key == signature and self.llm.poll() is None:
            return
        self.stop_chat()
        self.lease.acquire(update)
        if status["online"] and config["free_comfy"]:
            with suppress(OSError, RuntimeError):
                api(COMFY, "/free", {"unload_models": True, "free_memory": True})
        model = chat_model_path(key)
        projector = model.with_suffix(".mmproj.gguf")
        if not model.is_file() or not LU.is_file() or (vision and not projector.is_file()):
            raise RuntimeError("ไม่พบเอนจินหรือไฟล์โมเดลที่เลือก")
        with socket.socket() as port_probe:
            port_probe.bind(("127.0.0.1", 0))
            port = port_probe.getsockname()[1]
        args = [str(LU), "-m", str(model), "--host", "127.0.0.1", "--port", str(port),
                "--no-webui", *options]
        args += ["--mmproj", str(projector)] if vision else ["--no-mmproj"]
        self.llm_url = f"http://127.0.0.1:{port}"
        self.model_key = signature
        update("กำลังโหลด " + CHAT_MODELS[key][0])
        with (DATA / "chat-engine.log").open("wb") as log:
            self.llm = subprocess.Popen(args, cwd=LU.parent, stdin=subprocess.DEVNULL, stdout=log,
                                        stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(170):
            if self.llm.poll() is not None:
                break
            try:
                if api(self.llm_url, "/health", timeout=2)["status"] == "ok":
                    return
            except (OSError, RuntimeError):
                time.sleep(1)
        self.stop_chat()
        raise RuntimeError("โหลดโมเดลแชทไม่สำเร็จ ดูรายละเอียดใน chat-engine.log")

    def chat(self, payload, update, agent=False):
        config = preferences.DEFAULTS | payload.get("settings", {})
        vision = bool(payload.get("image"))
        actions = preferences.allowed_actions(config) if agent else []
        if agent and not actions:
            raise ValueError("เปิดสิทธิ์ให้ Agent อย่างน้อยหนึ่งรายการในหน้าตั้งค่า")
        self.start_chat(payload["model"], vision, config, agent, update)
        update("กำลังวิเคราะห์คำสั่ง" if agent else "กำลังตอบ")
        if agent:
            messages = [{"role": "system", "content": (
                'Return one JSON object: {"action":"status|list|read|write|create",'
                '"file":"simple filename.ext","text":"file content or media prompt",'
                '"recipe":"flux"}. '
                f"Pick a single action from {', '.join(actions)}. "
                "status checks the PC or queue; list lists the workspace; "
                "read and write operate on simple filenames; create submits a media job. "
                'If the request cannot be performed with these actions, return {"action":"unsupported"}.'
            )}, {"role": "user", "content": payload["text"]}]
        else:
            content = payload["text"]
            if vision:
                picture = uploaded(payload["image"])
                mime = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}[picture.suffix]
                encoded = base64.b64encode(picture.read_bytes()).decode("ascii")
                content = [{"type": "text", "text": content},
                           {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}]
            messages = []
            role = personas.PROMPTS.get(payload.get("persona"), "")
            custom = config["system_prompt"]
            system = custom
            if role:
                system = (role + "\n\nUse the language of the user's latest message unless "
                          "the user or the role explicitly requests another language.")
            if role and custom.strip():
                system += "\n\nUser's standing instructions take precedence over role guidance:\n" + custom
            if system.strip():
                messages.append({"role": "system", "content": system})
            messages.extend(payload.get("history", []))
            messages.append({"role": "user", "content": content})
        body = {"messages": messages, **preferences.request_options(config, agent)}
        try:
            reply = api(self.llm_url, "/v1/chat/completions", body, timeout=config["timeout"])
        except (TimeoutError, OSError):
            self.stop_chat()
            raise RuntimeError("เอนจินแชทหยุดตอบระหว่างประมวลผล") from None
        choice = reply["choices"][0]
        answer = choice["message"].get("content")
        reasoning = choice["message"].get("reasoning_content")
        if not isinstance(answer, str) or not answer.strip():
            if not agent and reasoning and choice.get("finish_reason") == "length":
                answer = "โมเดลใช้งบโทเคนครบระหว่างคิด ลองเพิ่มโทเคนคำตอบหรือลดงบการคิด"
            else:
                raise RuntimeError("โมเดลไม่ได้ส่งคำตอบ")
        if agent:
            try:
                candidate = json.loads(answer)
            except ValueError:
                raise ValueError("Agent ส่งแผนไม่ครบ ลองเพิ่มโทเคนสำหรับแผน Agent หรือย่อคำสั่ง") from None
            plan = validate_plan(candidate)
            if plan["action"] not in actions:
                raise ValueError("สิทธิ์ของ Agent สำหรับคำสั่งนี้ถูกปิดในหน้าตั้งค่า")
            return plan
        result = {"text": answer}
        if config["show_reasoning"] and isinstance(reasoning, str) and reasoning.strip():
            result["reasoning"] = reasoning
        usage = reply.get("usage", {})
        if isinstance(usage.get("completion_tokens"), int):
            result["tokens"] = usage["completion_tokens"]
        return result

    def start_comfy(self, update):
        if comfy_status()["online"]:
            return
        configured_url = CONNECTIONS.get("comfy_url")
        python = Path(CONNECTIONS.get("comfy_python", ""))
        main = Path(CONNECTIONS.get("comfy_main", ""))
        if configured_url != COMFY or not python.is_file() or not main.is_file():
            raise RuntimeError("Open ComfyUI and check its local URL before submitting a job.")
        if self.comfy is None or self.comfy.poll() is not None:
            args = [str(python), "-s", str(main), "--windows-standalone-build", "--disable-auto-launch",
                    "--listen", "127.0.0.1", "--port", str(address.port or 80)]
            if CONNECTIONS.get("comfy_cpu") is True:
                args.append("--cpu")
            log_path = DATA / "comfy-engine.log"
            with log_path.open("ab") as log:
                self.comfy = subprocess.Popen(args, cwd=main.parent.parent, stdout=log, stderr=subprocess.STDOUT,
                                              stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        update("กำลังเปิด ComfyUI ที่ติดตั้งไว้")
        until = time.monotonic() + 150
        while time.monotonic() < until:
            if self.comfy.poll() is not None:
                break
            if comfy_status()["online"]:
                return
            time.sleep(1)
        if self.comfy.poll() is None:
            self.comfy.terminate()
        raise RuntimeError("ComfyUI did not start. See comfy-engine.log in the TandemForge data folder.")

    def media(self, job_id, payload, update, remember, prompt_id=None):
        self.stop_chat()
        self.lease.acquire(update)
        try:
            return self._media(job_id, payload, update, remember, prompt_id)
        finally:
            self.lease.release()

    def _media(self, job_id, payload, update, remember, prompt_id=None):
        recipe = payload["recipe"]
        if not prompt_id:
            self.start_comfy(update)
            prefix = f"{FOLDER}/{job_id}/{recipe}"
            image_name = upload_comfy_image(source_image(payload), job_id) if RECIPES[recipe].get("input") else None
            graph = recipe_graph(recipe, payload, prefix, image_name)
            update("กำลังส่งเข้า ComfyUI")
            res = api(COMFY, "/prompt", {"prompt": graph, "client_id": f"studio-{job_id}"}, timeout=35)
            prompt_id = res["prompt_id"]
            remember(prompt_id)
        high = 0
        missing = 0
        interrupted = False
        offline = 0
        while True:
            try:
                hist = api(COMFY, f"/history/{prompt_id}").get(prompt_id)
                queue = None if hist else comfy_queue()
                offline = 0
            except OSError:
                offline += 1
                if offline >= 10:
                    raise RuntimeError("ติดต่อ ComfyUI ไม่ได้ระหว่างติดตามงาน") from None
                update("กำลังเชื่อมต่อ ComfyUI ใหม่")
                time.sleep(5)
                continue
            if hist:
                status = hist["status"]
                if status["status_str"] != "success":
                    if interrupted:
                        raise RuntimeError("หยุดงานเมื่อยอดจองหน่วยความจำใกล้เต็มต่อเนื่อง")
                    error = next((info for event, info in status["messages"] if event == "execution_error"), {})
                    raise RuntimeError(error.get("exception_message", "ComfyUI หยุดงานหรือสร้างสื่อไม่สำเร็จ")[:700])
                outputs = []
                for values in hist["outputs"].values():
                    for items in values.values():
                        if not isinstance(items, list):
                            continue
                        for item in items:
                            if isinstance(item, dict):
                                asset = save_comfy_image(item, job_id)
                                if asset and asset not in outputs:
                                    outputs.append(asset)
                if not outputs:
                    raise RuntimeError("ComfyUI จบงานแล้ว แต่ไม่พบไฟล์ผลลัพธ์ในโฟลเดอร์แอป")
                return {"media": outputs}
            active = any(item[1] == prompt_id for item in queue["queue_running"])
            pending = any(item[1] == prompt_id for item in queue["queue_pending"])
            missing = missing + 1 if not (active or pending) else 0
            if missing >= 4:
                raise RuntimeError("ไม่พบงานในคิวหรือประวัติ ComfyUI")
            commit = commit_percent()
            high = high + 1 if active and commit is not None and commit >= 96 else 0
            if high >= 3 and not interrupted:
                with suppress(ValueError):
                    api(COMFY, "/interrupt", {"prompt_id": prompt_id})
                interrupted = True
            update("รอหยุดงานเนื่องจากหน่วยความจำใกล้เต็ม" if interrupted else
                   "ComfyUI กำลังสร้างสื่อ" if active else "รอในคิว ComfyUI")
            time.sleep(5)


def workspace_file(name):
    if (not isinstance(name, str) or not re.fullmatch(r"[\w .-]{1,75}\.(txt|md|json|py|csv)", name, re.I)
            or os.path.isreserved(name)):
        raise ValueError("ใช้ชื่อไฟล์สั้น ๆ เช่น storyboard.md")
    path = (WORK / name).resolve()
    if not path.is_relative_to(WORK.resolve()):
        raise ValueError("ไฟล์ต้องอยู่ในพื้นที่ Agent")
    return path


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("action") not in AGENT_ACTIONS:
        raise ValueError("Agent รองรับตรวจสถานะ ดูไฟล์ อ่านไฟล์ เขียนไฟล์ใหม่ และส่งงานสร้างสื่อ")
    action = plan["action"]
    result = {"action": action, "label": AGENT_ACTIONS[action]}
    if action in ("read", "write"):
        workspace_file(plan.get("file"))
        result["file"] = plan["file"]
    if action in ("write", "create"):
        value = plan.get("text")
        if not isinstance(value, str) or not value.strip() or len(value) > 5000:
            raise ValueError("ข้อความสำหรับคำสั่ง Agent ต้องมีความยาว 1–5,000 ตัวอักษร")
        result["text"] = value
    if action == "create":
        if plan.get("recipe") not in RECIPES or RECIPES[plan["recipe"]].get("input"):
            raise ValueError("เลือกงานสร้างจากข้อความ หรือแนบภาพในแท็บสร้าง")
        result["recipe"] = plan["recipe"]
    return result


def execute_plan(plan):
    action = plan["action"]
    if action == "status":
        status = comfy_status()
        online = "ออนไลน์" if status["online"] else "ออฟไลน์"
        return f'ComfyUI {online} · กำลังทำ {status["running"]} · รอ {status["pending"]}'
    if action == "list":
        return "\n".join(sorted(path.name for path in WORK.iterdir() if path.is_file())[:100]) or "พื้นที่ Agent ยังว่าง"
    file = workspace_file(plan["file"])
    if action == "read":
        with file.open(encoding="utf-8-sig", errors="replace") as stream:
            return stream.read(8000)
    with file.open("x", encoding="utf-8") as stream:
        stream.write(plan["text"])
    return "บันทึก " + file.name + " แล้ว"
