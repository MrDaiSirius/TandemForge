import argparse
import hmac
import json
import mimetypes
import re
import secrets
import sqlite3
import sys
import threading
import time
import webbrowser
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

import engine
import model_guide
import personas
import preferences

DATABASE = engine.DATA / "studio.db"
STATIC = engine.ROOT / "dist"
MAX_IMAGE = 16 * 1024 * 1024
COOKIE = "tandemforge_session"
SESSION_SECONDS = 30 * 24 * 60 * 60
WAKE = threading.Event()


def database():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def change(sql, values=()):
    with closing(database()) as db, db:
        return db.execute(sql, values).rowcount


def rows(sql, values=()):
    with closing(database()) as db:
        return db.execute(sql, values).fetchall()


def setup():
    for folder in (engine.DATA, engine.UPLOADS, engine.WORK, engine.DATA / "bin", engine.DATA / "models"):
        folder.mkdir(parents=True, exist_ok=True)
    change("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, state TEXT NOT NULL, phase TEXT NOT NULL,
        created REAL NOT NULL, payload TEXT NOT NULL, result TEXT, error TEXT, prompt_id TEXT,
        approved INTEGER NOT NULL DEFAULT 0)""")
    change("""UPDATE jobs SET state='error', phase='', error='แอปปิดระหว่างประมวลผล กรุณาตรวจคิวแล้วส่งใหม่'
              WHERE state='running' AND (kind!='media' OR prompt_id IS NULL)""")
    change("""UPDATE jobs SET payload=json_remove(payload,'$.history')
              WHERE kind='chat' AND state IN ('done','error','cancelled')
                AND json_type(payload,'$.history') IS NOT NULL""")
    change("""CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY CHECK (id=1), revision INTEGER NOT NULL, content TEXT NOT NULL)""")
    starter = {}
    model = engine.CONNECTIONS.get("starter_model")
    if isinstance(model, str) and model in engine.CHAT_MODELS:
        starter.update(chat_model=model, agent_model=model)
        context = engine.CONNECTIONS.get("starter_context")
        if type(context) is int and 2048 <= context <= 4096:
            starter["context"] = context
    if engine.CONNECTIONS.get("starter_cpu") is True:
        starter["gpu_layers"] = 0
    change("INSERT OR IGNORE INTO preferences (id,revision,content) VALUES (1,0,?)",
           (json.dumps({"global": starter, "models": {}}),))


def read_settings(db):
    row = db.execute("SELECT revision,content FROM preferences WHERE id=1").fetchone()
    return row["revision"], json.loads(row["content"])


def settings_document(revision, saved):
    return {"revision": revision, "schema": preferences.SCHEMA, "defaults": preferences.DEFAULTS,
            "presets": preferences.PRESETS, **saved}


def settings_view():
    with closing(database()) as db:
        revision, saved = read_settings(db)
    return settings_document(revision, saved)


def save_settings(body):
    scope = body.get("scope")
    if scope != "global" and scope not in engine.CHAT_MODELS:
        raise ValueError("เลือกค่ากลางหรือโมเดลที่รองรับ")
    values = body.get("values")
    preferences.validate_values(values, engine.CHAT_MODELS, model_scope=scope != "global")
    with closing(database()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        revision, saved = read_settings(db)
        if type(body.get("revision")) is not int or body["revision"] != revision:
            return None
        if scope == "global":
            saved["global"] = values
        else:
            if values:
                saved["models"][scope] = values
            else:
                saved["models"].pop(scope, None)
        preferences.validate_effective(preferences.effective(saved))
        for key in saved["models"].keys() & engine.CHAT_MODELS.keys():
            try:
                preferences.validate_effective(preferences.effective(saved, key))
            except ValueError as exc:
                raise ValueError(f"{engine.CHAT_MODELS[key][0]} · {exc}") from None
        db.execute("UPDATE preferences SET revision=?,content=? WHERE id=1",
                   (revision + 1, json.dumps(saved, ensure_ascii=False)))
    return settings_document(revision + 1, saved)


def submit(kind, payload):
    job_id = secrets.token_hex(12)
    change("INSERT INTO jobs (id,kind,state,phase,created,payload) VALUES (?,?,'queued','รอคิว',?,?)",
           (job_id, kind, time.time(), json.dumps(payload, ensure_ascii=False)))
    WAKE.set()
    return {"id": job_id}


def public_job(row):
    payload = json.loads(row["payload"])
    return {
        "id": row["id"], "kind": row["kind"], "state": row["state"], "phase": row["phase"],
        "created": row["created"], "label": (engine.RECIPES[payload["recipe"]]["label"]
                                             if row["kind"] == "media" else row["kind"]),
        "text": payload.get("text"), "result": json.loads(row["result"]) if row["result"] else None,
        "error": row["error"], "approved": bool(row["approved"]),
    }


def worker(engines, stop):
    last_job = time.monotonic()
    try:
        while not stop.is_set():
            engines.yield_if_requested()
            WAKE.clear()
            batch = rows("""SELECT * FROM jobs WHERE state='queued' OR (state='running' AND kind='media')
                            ORDER BY (state='running') DESC, created LIMIT 1""")
            if not batch:
                if engines.llm and time.monotonic() - last_job >= engines.idle_seconds:
                    engines.stop_chat()
                WAKE.wait(2)
                continue
            row = batch[0]
            key, kind = row["id"], row["kind"]
            if not change("UPDATE jobs SET state='running',phase='กำลังเริ่ม' WHERE id=? AND state IN ('queued','running')", (key,)):
                continue

            def phase(message):
                change("UPDATE jobs SET phase=? WHERE id=? AND phase<>?", (message, key, message))

            def remember(prompt_id):
                change("UPDATE jobs SET prompt_id=? WHERE id=?", (prompt_id, key))

            try:
                payload = json.loads(row["payload"])
                if kind == "media":
                    result = engines.media(key, payload, phase, remember, row["prompt_id"])
                else:
                    result = engines.chat(payload, phase, agent=kind == "agent")
                change("""UPDATE jobs SET state='done',phase='',result=?,
                          payload=json_remove(payload,'$.history') WHERE id=?""",
                       (json.dumps(result, ensure_ascii=False), key))
            except Exception as exc:
                message = str(exc)[:1000] or type(exc).__name__
                print(f"Job {key} failed: {type(exc).__name__}", flush=True)
                change("""UPDATE jobs SET state='error',phase='',error=?,
                          payload=json_remove(payload,'$.history') WHERE id=?""", (message, key))
            finally:
                if engines.llm is None:
                    engines.lease.release()
                last_job = time.monotonic()
    finally:
        engines.stop_chat()


def checked_text(payload, limit=5000):
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > limit:
        raise ValueError(f"ใส่ข้อความ 1–{limit:,} ตัวอักษร")
    return text.strip()


def media_payload(body):
    recipe = body.get("recipe")
    if recipe not in engine.RECIPES:
        raise ValueError("เลือกประเภทงานที่รองรับ")
    payload = {"recipe": recipe, "text": checked_text(body)}
    if recipe == "flux" and "size" in body:
        size = body["size"]
        if not isinstance(size, str) or size not in engine.IMAGE_SIZES:
            raise ValueError("เลือกขนาดภาพจากรายการในแอป")
        payload["size"] = size
    if engine.RECIPES[recipe].get("input"):
        payload.update(image=body.get("image"), source=body.get("source"))
        engine.source_image(payload)
    return payload


def chat_choices():
    image_models = [key for key in engine.CHAT_MODELS if engine.has_projector(key)]
    return image_models, preferences.available_chat_tasks(engine.CHAT_MODELS, image_models)


def chat_payload(body, agent=False):
    with closing(database()) as db:
        _, saved = read_settings(db)
    defaults = preferences.effective(saved)
    configured = defaults["agent_model" if agent else "chat_model"]
    task_id = "" if agent else body.get("task", "")
    if not isinstance(task_id, str):
        raise ValueError("เลือกโหมดงานจากรายการในแอป")
    if task_id:
        _, tasks = chat_choices()
        if task_id not in tasks:
            raise ValueError("โหมดงานนี้ยังไม่มีโมเดลที่รองรับ")
        configured = tasks[task_id]["model"]
    model = body.get("model", configured if configured in engine.CHAT_MODELS else next(iter(engine.CHAT_MODELS), ""))
    if not engine.CHAT_MODELS:
        raise ValueError("Add a local GGUF model and restart TandemForge.")
    if model not in engine.CHAT_MODELS:
        raise ValueError("เลือกโมเดลแชท")
    config = preferences.effective(saved, model)
    if task_id:
        if model != configured:
            raise ValueError("เลือกโมเดลที่ตรงกับโหมดงาน หรือลองโหมดกำหนดเอง")
        preferences.apply_chat_task(config, task_id)
    payload = {"model": model, "text": checked_text(body, 3500), "settings": config}
    if agent and not preferences.allowed_actions(config):
        raise ValueError("เปิดสิทธิ์ให้ Agent อย่างน้อยหนึ่งรายการในหน้าตั้งค่า")
    if not agent:
        persona = body.get("persona", "")
        if not isinstance(persona, str) or (persona and persona not in personas.PROMPTS):
            raise ValueError("เลือก Persona จากรายการในแอป")
        if persona:
            payload["persona"] = persona
        if body.get("image"):
            if not config["vision"]:
                raise ValueError("การแนบภาพถูกปิดสำหรับโมเดลนี้")
            if not engine.has_projector(model):
                raise ValueError("เพิ่มไฟล์ตัวอ่านภาพที่ตรงกับโมเดลนี้ก่อนแนบภาพ")
            engine.uploaded(body["image"])
            payload["image"] = body["image"]
        history = body.get("history", [])
        if not isinstance(history, list):
            raise ValueError("ประวัติแชทไม่ถูกต้อง")
        count = config["history_messages"]
        payload["history"] = [
            {"role": line["role"], "content": line["content"][:1800]}
            for line in (history[-count:] if count else []) if isinstance(line, dict) and line.get("role") in ("user", "assistant")
            and isinstance(line.get("content"), str)
        ]
    return payload


class StudioServer(ThreadingHTTPServer):
    def __init__(self, address, code, session_key):
        super().__init__(address, StudioHandler)
        self.code = code
        self.session_key = session_key
        self.auth_lock = threading.Lock()
        self.login_attempts = []

    def session_token(self, expires):
        signed = f"{expires}:{self.code}".encode()
        signature = hmac.digest(self.session_key, signed, "sha256").hex()
        return f"{expires}.{signature}"


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def authenticated(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        found = cookie.get(COOKIE)
        token = re.fullmatch(r"([0-9]{1,12})\.[0-9a-f]{64}", found.value) if found else None
        if not token:
            return False
        expires = int(token[1])
        return expires > time.time() and hmac.compare_digest(found.value, self.server.session_token(expires))

    def valid_host(self):
        host = self.headers.get("Host", "").lower()
        return bool(re.fullmatch(r"(?:127\.0\.0\.1|localhost|[a-z0-9.-]+\.ts\.net)(?::\d{1,5})?", host))

    def same_origin(self):
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        parsed = urlsplit(origin)
        return parsed.scheme in ("https", "http") and parsed.netloc.lower() == self.headers.get("Host", "").lower()

    def headers_for(self, code, kind, size, headers=()):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; img-src 'self' blob: data:; media-src 'self'; "
                         "script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; "
                         "base-uri 'none'; form-action 'self'")
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()

    def reply(self, status, data, headers=()):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.headers_for(status, "application/json; charset=utf-8", len(raw), headers)
        self.wfile.write(raw)

    def send_file(self, path, media=False):
        kind = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with path.open("rb") as stream:
            size = path.stat().st_size
            start, end = 0, size - 1
            extra = [("Accept-Ranges", "bytes")] if media else []
            requested = self.headers.get("Range") if media else None
            if requested:
                match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested)
                if match and (match[1] or match[2]):
                    start = int(match[1]) if match[1] else max(0, size - int(match[2]))
                    end = min(size - 1, int(match[2])) if match[1] and match[2] else size - 1
                if not match or not (match[1] or match[2]) or not 0 <= start <= end < size:
                    self.headers_for(416, kind, 0, [("Content-Range", f"bytes */{size}")])
                    return
                extra.append(("Content-Range", f"bytes {start}-{end}/{size}"))
            left = end - start + 1
            self.headers_for(206 if requested else 200, kind, left, extra)
            stream.seek(start)
            while left:
                data = stream.read(min(left, 256 * 1024))
                if not data:
                    break
                self.wfile.write(data)
                left -= len(data)

    def read_body(self, limit):
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= limit:
            raise ValueError("ข้อมูลมีขนาดเกินกำหนดหรือว่างเปล่า")
        self.connection.settimeout(25)
        return self.rfile.read(size)

    def require_session(self):
        if self.authenticated():
            return True
        self.reply(401, {"error": "ใส่รหัสเข้าแอปก่อน"})
        return False

    def do_GET(self):
        if not self.valid_host():
            self.reply(421, {"error": "ที่อยู่แอปไม่ถูกต้อง"})
            return
        url = urlsplit(self.path)
        try:
            if url.path == "/api/session":
                self.reply(200, {"authenticated": self.authenticated()})
            elif url.path.startswith(("/api/", "/media/")):
                if self.require_session():
                    self.private_get(url)
            else:
                static = STATIC / ("index.html" if url.path == "/" else url.path.lstrip("/"))
                if static.parent == STATIC and static.is_file():
                    self.send_file(static)
                else:
                    self.reply(404, {"error": "ไม่พบหน้า"})
        except (ConnectionError, TimeoutError):
            pass
        except (ValueError, OSError, RuntimeError) as exc:
            self.reply(404, {"error": str(exc)})

    def private_get(self, url):
        path = url.path
        if path == "/api/info":
            image_models, tasks = chat_choices()
            self.reply(200, {"recipes": engine.RECIPES, "models": {k: v[0] for k, v in engine.CHAT_MODELS.items()},
                             "image_models": image_models, "chat_tasks": tasks,
                             "personas": personas.choices(), "chat_ready": engine.LU.is_file() and bool(engine.CHAT_MODELS),
                             "comfy": engine.comfy_status(),
                             "commit": engine.commit_percent()})
        elif path == "/api/settings":
            self.reply(200, settings_view())
        elif path == "/api/model-guide":
            self.reply(200, model_guide.guide(engine.MODELS))
        elif path == "/api/jobs":
            kind = parse_qs(url.query).get("kind", ["media"])[0]
            if kind not in ("media", "agent"):
                raise ValueError("ไม่พบหมวดประวัติ")
            result = rows("SELECT * FROM jobs WHERE kind=? ORDER BY created DESC LIMIT 60", (kind,))
            self.reply(200, {"jobs": [public_job(row) for row in result]})
        elif path.startswith("/api/jobs/"):
            found = rows("SELECT * FROM jobs WHERE id=?", (path.rsplit("/", 1)[1],))
            self.reply(200, public_job(found[0])) if found else self.reply(404, {"error": "ไม่พบงาน"})
        elif path.startswith("/media/"):
            self.send_file(engine.app_output(unquote(path.removeprefix("/media/"))), media=True)
        else:
            self.reply(404, {"error": "ไม่พบเส้นทาง"})

    def login(self, data):
        now = time.monotonic()
        with self.server.auth_lock:
            attempts = self.server.login_attempts
            attempts[:] = [attempt for attempt in attempts if now - attempt < 60]
            if len(attempts) >= 8:
                self.reply(429, {"error": "ลองใหม่อีกครั้งในหนึ่งนาที"})
                return
            code = str(data.get("code", "")).strip().upper().encode()
            if not hmac.compare_digest(code, self.server.code.encode()):
                attempts.append(now)
                self.reply(401, {"error": "รหัสไม่ตรง ลองดูรหัสที่หน้าต่างบนคอม"})
                return
            attempts.clear()
        secure = "; Secure" if self.headers.get("Host", "").split(":")[0].lower().endswith(".ts.net") else ""
        session = self.server.session_token(int(time.time()) + SESSION_SECONDS)
        self.reply(200, {"authenticated": True},
                   [("Set-Cookie", f"{COOKIE}={session}; Max-Age={SESSION_SECONDS}; Path=/; HttpOnly; SameSite=Strict{secure}")])

    def do_POST(self):
        if not self.valid_host() or not self.same_origin():
            self.reply(403, {"error": "ต้นทางคำขอไม่ตรงกับแอป"})
            return
        path = urlsplit(self.path).path
        try:
            if path != "/api/login" and not self.require_session():
                return
            if path == "/api/upload":
                raw = self.read_body(MAX_IMAGE)
                name = secrets.token_hex(16) + engine.image_extension(raw)
                (engine.UPLOADS / name).write_bytes(raw)
                self.reply(201, {"image": name})
                return
            if self.headers.get_content_type() != "application/json":
                raise ValueError("คำขอต้องเป็น JSON")
            body = json.loads(self.read_body((192 if path == "/api/chat" else 64) * 1024))
            if not isinstance(body, dict):
                raise ValueError("ข้อมูลไม่ถูกต้อง")
            if path == "/api/login":
                self.login(body)
            elif path == "/api/create":
                self.reply(202, submit("media", media_payload(body)))
            elif path in ("/api/chat", "/api/agent"):
                kind = path.rsplit("/", 1)[1]
                self.reply(202, submit(kind, chat_payload(body, agent=kind == "agent")))
            elif path == "/api/settings":
                saved = save_settings(body)
                self.reply(200, saved) if saved else self.reply(409, {"error": "ค่าตั้งถูกแก้จากอีกหน้าจอ กรุณาโหลดค่าล่าสุด"})
            elif path == "/api/approve":
                self.approve(body)
            elif path == "/api/cancel":
                count = change("""UPDATE jobs SET state='cancelled',phase='',payload=json_remove(payload,'$.history')
                                  WHERE id=? AND state='queued'""", (str(body.get("id")),))
                self.reply(200 if count else 409, {"cancelled": True} if count else {"error": "ยกเลิกได้เฉพาะงานที่ยังรอคิว"})
            elif path == "/api/delete-history":
                self.delete_history(body)
            else:
                self.reply(404, {"error": "ไม่พบเส้นทาง"})
        except (ValueError, TypeError, RuntimeError, OSError) as exc:
            self.reply(400, {"error": str(exc)})

    def delete_history(self, body):
        key = body.get("id")
        if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{24}", key):
            raise ValueError("รหัสรายการประวัติไม่ถูกต้อง")
        with closing(database()) as db, db:
            db.execute("DELETE FROM jobs WHERE id=? AND state IN ('done','error','cancelled')", (key,))
            active = db.execute("SELECT 1 FROM jobs WHERE id=?", (key,)).fetchone()
        if active:
            self.reply(409, {"error": "ลบประวัติได้เมื่องานเสร็จหรือยกเลิกแล้ว"})
        else:
            self.reply(200, {"deleted": True})

    def approve(self, body):
        key = str(body.get("id"))
        with closing(database()) as db, db:
            claim = db.execute("""UPDATE jobs SET approved=1
                                  WHERE id=? AND kind='agent' AND state='done' AND approved=0
                                  RETURNING result""", (key,)).fetchone()
            if not claim:
                raise ValueError("คำสั่งนี้ถูกอนุมัติแล้วหรือยังไม่พร้อม")
            plan = engine.validate_plan(json.loads(claim["result"]))
            _, saved = read_settings(db)
            if plan["action"] not in preferences.allowed_actions(preferences.effective(saved)):
                raise ValueError("สิทธิ์ของ Agent สำหรับคำสั่งนี้ถูกปิดในหน้าตั้งค่า")
            if plan["action"] == "create":
                payload = media_payload(plan)
                media_id = secrets.token_hex(12)
                db.execute("""INSERT INTO jobs (id,kind,state,phase,created,payload)
                              VALUES (?,'media','queued','รอคิว',?,?)""",
                           (media_id, time.time(), json.dumps(payload, ensure_ascii=False)))
                result = {"id": media_id}
            else:
                result = {"text": engine.execute_plan(plan)}
            stored = dict(plan, execution=result)
            db.execute("UPDATE jobs SET result=? WHERE id=?", (json.dumps(stored, ensure_ascii=False), key))
        WAKE.set()
        self.reply(200, result)


def load_or_create(path, default):
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(default + "\n")
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8").strip()


def main():
    if sys.version_info < (3, 13):
        raise RuntimeError("TandemForge requires Python 3.13 or newer.")
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=8770)
    cli.add_argument("--quiet", action="store_true")
    cli.add_argument("--open", action="store_true")
    args = cli.parse_args()
    engine.DATA.mkdir(parents=True, exist_ok=True)
    generated = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(10))
    code = load_or_create(engine.DATA / "access-code.txt", generated)
    if not re.fullmatch(r"[A-Z0-9]{6,10}", code):
        raise ValueError("รหัสใน access-code.txt ต้องมีตัวเลขหรือตัวอักษร A–Z จำนวน 6–10 ตัว")
    key = bytes.fromhex(load_or_create(engine.DATA / "session-key.txt", secrets.token_hex(32)))
    if len(key) != 32:
        raise ValueError("session-key.txt มีขนาดไม่ถูกต้อง")
    # Bind before touching jobs so a second launcher can't reset active work.
    with StudioServer(("127.0.0.1", args.port), code, key) as server:
        setup()
        engines = engine.Engines()
        stop = threading.Event()
        thread = threading.Thread(target=worker, args=(engines, stop), daemon=True)
        thread.start()
        print(f"TandemForge - http://127.0.0.1:{args.port}", flush=True)
        if not args.quiet:
            print("Access code: " + code, flush=True)
        if args.open:
            threading.Timer(0.25, webbrowser.open, (f"http://127.0.0.1:{args.port}",)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            WAKE.set()
            engines.stop_chat()


if __name__ == "__main__":
    main()
