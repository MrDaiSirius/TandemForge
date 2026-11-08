import math


def field(key, label, kind, default, **options):
    return {"key": key, "label": label, "kind": kind, "default": default, **options}


CACHE_TYPES = ("f16", "bf16", "f32", "q8_0", "q4_0", "q4_1", "iq4_nl", "q5_0", "q5_1")
SCHEMA = {
    "ทั่วไป": [
        field("chat_model", "โมเดลเริ่มต้นสำหรับแชท", "model", "qwen9", global_only=True),
        field("agent_model", "โมเดลเริ่มต้นสำหรับ Agent", "model", "qwen9", global_only=True),
        field("theme", "ธีม", "choice", "dark", choices={"dark": "มืด", "light": "สว่าง", "system": "ตามเครื่อง"}, global_only=True),
        field("enter_to_send", "กด Enter เพื่อส่งแชท", "bool", False, global_only=True, hint="Shift+Enter ขึ้นบรรทัดใหม่"),
        field("system_prompt", "คำสั่งประจำสำหรับแชท", "text", "", max=4000,
              hint="เช่น ตอบภาษาไทยและอธิบายโค้ดพร้อมตัวอย่าง"),
        field("history_messages", "จำนวนข้อความย้อนหลัง", "int", 6, min=0, max=20, hint="0 ใช้เฉพาะข้อความล่าสุด"),
    ],
    "การตอบและการสุ่ม": [
        field("temperature", "Temperature", "float", 0.55, min=0, max=2, step=0.05),
        field("top_p", "Top P", "float", 0.95, min=0, max=1, step=0.01),
        field("top_k", "Top K", "int", 40, min=0, max=200, hint="0 ปิด Top K"),
        field("min_p", "Min P", "float", 0.05, min=0, max=1, step=0.01),
        field("max_tokens", "โทเคนคำตอบสูงสุด", "int", 900, min=0, max=32768, hint="0 คำนวณจากขนาด Context"),
        field("seed", "Seed", "int", -1, min=-1, max=4294967294, hint="-1 สุ่มใหม่ทุกครั้ง"),
        field("repeat_penalty", "Repeat penalty", "float", 1, min=0.1, max=3, step=0.01),
        field("repeat_last_n", "ช่วงย้อนหลังสำหรับ Repeat penalty", "int", 64, min=-1, max=32768),
        field("presence_penalty", "Presence penalty", "float", 0, min=-2, max=2, step=0.05),
        field("frequency_penalty", "Frequency penalty", "float", 0, min=-2, max=2, step=0.05),
        field("typical_p", "Typical P", "float", 1, min=0, max=1, step=0.01),
        field("stop", "ข้อความที่ใช้หยุดคำตอบ", "text", "", max=512, hint="หนึ่งข้อความต่อบรรทัด"),
        field("cache_prompt", "ใช้แคชข้อความก่อนหน้า", "bool", True),
    ],
    "เอนจินและหน่วยความจำ": [
        field("context", "Context (โทเคน)", "int", 4096, min=512, max=131072, step=256),
        field("gpu_layers", "จำนวนเลเยอร์บน GPU", "int", -2, min=-2, max=200,
              hint="-2 ปรับให้พอดีอัตโนมัติ · -1 ทั้งหมด · 0 ใช้ CPU · จำนวนบวกกำหนดเอง"),
        field("vram_margin", "พื้นที่สำรอง VRAM (MiB)", "int", 2304, min=256, max=12000, step=128,
              hint="ใช้เมื่อเลือก GPU แบบอัตโนมัติ"),
        field("threads", "CPU threads", "int", -1, min=-1, max=32, hint="-1 อัตโนมัติ"),
        field("threads_batch", "CPU threads ตอนอ่านพรอมป์", "int", -1, min=-1, max=32, hint="-1 ใช้ค่า CPU threads"),
        field("batch_size", "Batch size", "int", 2048, min=32, max=8192, step=32),
        field("ubatch_size", "Microbatch size", "int", 512, min=32, max=2048, step=32),
        field("flash_attn", "Flash Attention", "choice", "auto", choices={"auto": "อัตโนมัติ", "on": "เปิด", "off": "ปิด"}),
        field("cache_k", "KV cache · K", "choice", "f16", choices=CACHE_TYPES),
        field("cache_v", "KV cache · V", "choice", "f16", choices=CACHE_TYPES),
        field("kv_offload", "ย้าย KV cache ไป GPU", "bool", True),
        field("load_mode", "โหมดโหลดโมเดล (mmap / mlock)", "choice", "auto",
              choices={"auto": "อัตโนมัติ", "none": "โหลดเต็มเข้า RAM", "mmap": "mmap", "mlock": "mlock", "mmap+mlock": "mmap + mlock"}),
        field("warmup", "วอร์มโมเดลตอนเปิด", "bool", False),
        field("idle_seconds", "คืนหน่วยความจำแชทเมื่อว่าง (วินาที)", "int", 90, min=0, max=3600,
              hint="0 คืนทันทีเมื่อคิวว่าง"),
        field("timeout", "เวลารอคำตอบสูงสุด (วินาที)", "int", 240, min=30, max=1800, step=30),
        field("free_comfy", "ขอคืน VRAM จาก ComfyUI ก่อนโหลดแชท", "bool", True, global_only=True),
    ],
    "การคิดและภาพ": [
        field("reasoning", "โหมดคิด", "choice", "off", choices={"off": "ปิด", "auto": "ตามโมเดล", "on": "เปิด"}),
        field("reasoning_budget", "งบโทเคนการคิด", "int", -1, min=-1, max=32768,
              hint="-1 ใช้ค่าเอนจิน · ทำงานกับโมเดลที่รองรับ"),
        field("show_reasoning", "แสดงข้อความการคิดที่โมเดลส่งกลับ", "bool", False),
        field("vision", "อนุญาตให้แนบภาพ", "bool", True),
        field("mmproj_offload", "ย้ายตัวอ่านภาพไป GPU", "bool", True),
        field("image_min_tokens", "โทเคนภาพขั้นต่ำ", "int", -1, min=-1, max=16384, hint="-1 ใช้ค่าเอนจิน"),
        field("image_max_tokens", "โทเคนภาพสูงสุด", "int", -1, min=-1, max=16384, hint="-1 ใช้ค่าเอนจิน"),
    ],
    "Agent": [
        field("agent_temperature", "Temperature ของ Agent", "float", 0, min=0, max=1, step=0.05),
        field("agent_max_tokens", "โทเคนสำหรับแผน Agent", "int", 900, min=128, max=8192),
        field("agent_enabled", "เปิด Agent", "bool", True, global_only=True),
        field("agent_status", "อนุญาตตรวจสถานะเครื่อง", "bool", True, global_only=True),
        field("agent_read", "อนุญาตดูรายการและอ่านไฟล์", "bool", True, global_only=True),
        field("agent_write", "อนุญาตเขียนไฟล์ใหม่", "bool", True, global_only=True),
        field("agent_create", "อนุญาตส่งงานสร้างสื่อ", "bool", True, global_only=True),
    ],
}
FIELDS = {option["key"]: option for group in SCHEMA.values() for option in group}
DEFAULTS = {key: option["default"] for key, option in FIELDS.items()}
PRESETS = [
    {"id": "balanced", "label": "แชททั่วไป · สมดุล",
     "description": "เริ่มจาก Qwen 9B ใช้คุย สรุป และแปลในชีวิตประจำวัน",
     "values": {"temperature": 0.55, "top_p": 0.95, "top_k": 40, "min_p": 0.05,
                "context": 4096, "max_tokens": 900, "history_messages": 6, "reasoning": "off"}},
    {"id": "casual", "label": "คุยเล่น · คำตอบสั้น",
     "description": "คุยเป็นกันเอง ตอบสั้นลง และส่งบริบทล่าสุดเพิ่มอีกเล็กน้อย",
     "values": {"temperature": 0.75, "top_p": 0.95, "context": 4096, "max_tokens": 650,
                "history_messages": 8, "reasoning": "off"}},
    {"id": "rough", "label": "คุยเล่น · สายปากจัด",
     "description": "คู่กับ Persona สายปากจัด ลอง Qwen 9B Abliterated หรือ Orca 27B Uncensored",
     "values": {"temperature": 0.8, "top_p": 0.95, "context": 4096, "max_tokens": 800,
                "history_messages": 8, "repeat_penalty": 1, "reasoning": "off"}},
    {"id": "coding", "label": "เขียนโค้ดและแก้บั๊ก",
     "description": "ลดความสุ่มและเผื่อพื้นที่ให้ตัวอย่างโค้ดกับคำอธิบาย",
     "values": {"temperature": 0.2, "top_p": 0.95, "context": 4096, "max_tokens": 1500,
                "history_messages": 6, "repeat_penalty": 1, "reasoning": "off"}},
    {"id": "creative", "label": "เขียนบท นิยาย และสวมบท",
     "description": "เพิ่มความหลากหลายและความยาวสำหรับฉาก บทพูด และสตอรีบอร์ด",
     "values": {"temperature": 0.8, "top_p": 0.95, "context": 4096, "max_tokens": 1500,
                "history_messages": 8, "reasoning": "off"}},
    {"id": "analysis", "label": "คิดวิเคราะห์หลายขั้น",
     "description": "เปิดโหมดคิดให้โมเดลที่รองรับ พร้อมงบคิด 512 โทเคนและเวลารอเพิ่ม",
     "values": {"temperature": 0.3, "context": 4096, "max_tokens": 1700, "history_messages": 6,
                "reasoning": "on", "reasoning_budget": 512, "timeout": 360}},
    {"id": "vision", "label": "อ่านภาพและสกรีนช็อต",
     "description": "เปิดแนบภาพและใช้ GPU กับตัวอ่านภาพ เริ่มลองกับ Qwen 9B",
     "values": {"temperature": 0.3, "context": 4096, "max_tokens": 900, "history_messages": 4,
                "vision": True, "mmproj_offload": True, "image_min_tokens": -1, "image_max_tokens": -1,
                "reasoning": "off"}},
    {"id": "memory", "label": "ประหยัดหน่วยความจำ · สลับ ComfyUI",
     "description": "ใช้ Context 3,072 ลดขนาด Batch และคืนโมเดลแชทเมื่อว่าง 30 วินาที",
     "values": {"context": 3072, "max_tokens": 900, "gpu_layers": -2, "vram_margin": 3072,
                "batch_size": 1024, "ubatch_size": 256, "idle_seconds": 30, "warmup": False,
                "load_mode": "auto", "flash_attn": "auto", "cache_k": "f16", "cache_v": "f16"}},
    {"id": "long", "label": "อ่านข้อความยาว · Context 8,192",
     "description": "สำหรับโค้ดหรือบทที่ยาวขึ้น เริ่มทดสอบกับ 9B และดูการใช้หน่วยความจำ",
     "values": {"context": 8192, "max_tokens": 1500, "history_messages": 10, "gpu_layers": -2,
                "vram_margin": 2304, "batch_size": 1024, "ubatch_size": 256, "timeout": 360}},
    {"id": "agent", "label": "Agent · วางแผนและสั่งงาน",
     "description": "ลดความสุ่มของแผน และให้ Agent มีพื้นที่เขียนคำสั่ง 900 โทเคน",
     "values": {"agent_temperature": 0, "agent_max_tokens": 900}},
]
REQUEST_PARAMS = ("temperature", "top_p", "top_k", "min_p", "seed", "repeat_penalty", "repeat_last_n",
                  "presence_penalty", "frequency_penalty", "typical_p", "cache_prompt")
ACTION_KEYS = {"status": "agent_status", "list": "agent_read", "read": "agent_read",
               "write": "agent_write", "create": "agent_create"}


CHAT_TASKS = {
    "quick": ("คุยเร็ว", "ปิดโหมดคิด เหมาะกับแชทและงานสั้น ๆ",
              ("qwen9", "qwen9-stock"), {"reasoning": "off"}),
    "quality": ("งานหลายเงื่อนไข", "ลดความสุ่ม เหมาะกับการทำตามโจทย์ สรุป และช่วยดูโค้ด",
                ("gemma12", "qwen35"), {"temperature": 0.15, "reasoning": "off"}),
    "reason": ("คิดวิเคราะห์", "เปิดโหมดคิดและเผื่อโทเคนเพิ่ม คำตอบอาจใช้เวลานานขึ้น",
               ("qwen9", "qwen9-stock"), {"temperature": 0.15, "reasoning": "on", "reasoning_budget": -1}),
    "vision": ("อ่านภาพ", "เลือกโมเดลที่มีตัวอ่านภาพ แล้วแนบภาพจากช่องข้อความ",
               ("gemma12", "qwen9-stock", "qwen9"), {"temperature": 0.3, "reasoning": "off"}),
    "json": ("ส่งออก JSON", "จำกัดคำตอบให้เป็น JSON object เหมาะกับงานที่ต้องนำข้อมูลไปใช้ต่อ",
              ("gemma12", "qwen35", "qwen9-stock", "qwen9"), {"temperature": 0.1, "reasoning": "off",
                                                              "json_output": True}),
}


def available_chat_tasks(models, image_models):
    tasks = {}
    for key, (label, description, preferred, _) in CHAT_TASKS.items():
        candidates = image_models if key == "vision" else models
        model = next((name for name in preferred if name in candidates), None)
        if model is None and key in ("quick", "vision", "json"):
            model = next(iter(candidates), None)
        if model is not None:
            tasks[key] = {"label": label, "description": description, "model": model}
    return tasks


def apply_chat_task(config, key):
    config.update(CHAT_TASKS[key][3])
    if key == "reason" and config["max_tokens"]:
        config["max_tokens"] = max(config["max_tokens"], min(1536, config["context"] // 2))


def effective(saved, model=None):
    return DEFAULTS | saved.get("global", {}) | saved.get("models", {}).get(model, {})


def validate_values(values, model_names, model_scope=False):
    if not isinstance(values, dict):
        raise ValueError("ข้อมูลตั้งค่าต้องเป็น JSON object")
    for key, value in values.items():
        option = FIELDS.get(key)
        if option is None or (model_scope and option.get("global_only")):
            raise ValueError(f"ตัวเลือกนี้ใช้กับขอบเขตที่เลือกไม่ได้ ({key})")
        kind = option["kind"]
        if kind == "bool":
            valid = type(value) is bool
        elif kind == "int":
            valid = type(value) is int and option["min"] <= value <= option["max"]
        elif kind == "float":
            valid = type(value) in (int, float) and option["min"] <= value <= option["max"] and math.isfinite(value)
        elif kind == "choice":
            valid = isinstance(value, str) and value in option["choices"]
        elif kind == "model":
            valid = isinstance(value, str) and (value in model_names or value == option["default"])
        else:
            valid = isinstance(value, str) and len(value) <= option["max"] and "\x00" not in value
        if not valid:
            raise ValueError(f"ค่าของ {option['label']} อยู่นอกช่วงที่รองรับ")


def validate_effective(config):
    if config["max_tokens"] >= config["context"]:
        raise ValueError("โทเคนคำตอบสูงสุดต้องน้อยกว่า Context หรือใช้ 0 สำหรับอัตโนมัติ")
    if config["ubatch_size"] > config["batch_size"]:
        raise ValueError("Microbatch size ต้องไม่เกิน Batch size")
    if config["cache_v"] not in ("f16", "bf16", "f32") and config["flash_attn"] != "on":
        raise ValueError("KV cache V แบบ quantized ต้องเปิด Flash Attention")
    lower, upper = config["image_min_tokens"], config["image_max_tokens"]
    if lower != -1 and upper != -1 and lower > upper:
        raise ValueError("โทเคนภาพขั้นต่ำต้องไม่เกินโทเคนภาพสูงสุด")


def engine_options(config, vision, agent):
    args = ["-c", str(config["context"]), "-np", "1", "-t", str(config["threads"]),
            "-tb", str(config["threads_batch"]), "-b", str(config["batch_size"]),
            "-ub", str(config["ubatch_size"]), "--flash-attn", config["flash_attn"],
            "--cache-type-k", config["cache_k"], "--cache-type-v", config["cache_v"],
            "--load-mode", config["load_mode"]]
    layers = config["gpu_layers"]
    if layers == -2:
        args += ["--fit", "on", "--fit-target", str(config["vram_margin"])]
    else:
        args += ["--fit", "off", "--n-gpu-layers", "all" if layers == -1 else str(layers)]
    args += ["--kv-offload" if config["kv_offload"] else "--no-kv-offload",
             "--warmup" if config["warmup"] else "--no-warmup",
             "--reasoning", "off" if agent else config["reasoning"]]
    if not agent and config["reasoning"] != "off" and config["reasoning_budget"] >= 0:
        args += ["--reasoning-budget", str(config["reasoning_budget"])]
    if vision:
        args.append("--mmproj-offload" if config["mmproj_offload"] else "--no-mmproj-offload")
        for key in ("image_min_tokens", "image_max_tokens"):
            if config[key] != -1:
                args += ["--" + key.replace("_", "-"), str(config[key])]
    return args


def request_options(config, agent):
    result = {key: config[key] for key in REQUEST_PARAMS}
    result["max_tokens"] = config["max_tokens"] or min(2048, config["context"] // 2)
    if agent:
        result["temperature"] = config["agent_temperature"]
        result["max_tokens"] = min(config["agent_max_tokens"], config["context"] - 256)
        result["response_format"] = {"type": "json_object"}
    elif config.get("json_output"):
        result["response_format"] = {"type": "json_object"}
    elif config["stop"].strip():
        result["stop"] = [line.strip() for line in config["stop"].splitlines() if line.strip()][:16]
    return result


def allowed_actions(config):
    return [key for key, setting in ACTION_KEYS.items() if config["agent_enabled"] and config[setting]]
