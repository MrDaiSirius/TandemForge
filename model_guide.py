"""Conservative Windows model suggestions based on local hardware and file sizes."""

import ctypes
import shutil
import uuid
from pathlib import Path

GIB = 1024**3
CATALOG = (
    {
        "id": "qwen-2b", "chat_id": "qwen2-stock", "name": "Qwen 3.5 2B · Q4_K_M", "tier": "Compact",
        "file": "Qwen3.5-2B-Q4_K_M.gguf", "size": 1280835840,
        "repo": "unsloth/Qwen3.5-2B-GGUF", "revision": "f6d5376be1edb4d416d56da11e5397a961aca8ae",
        "vram": 3.75, "ram": 8, "cpu_ram": 8, "cpu_free": 3, "context": 2048,
    },
    {
        "id": "qwen-4b", "chat_id": "qwen4-stock", "name": "Qwen 3.5 4B · Q4_K_M", "tier": "Light",
        "file": "Qwen3.5-4B-Q4_K_M.gguf", "size": 2740937888,
        "repo": "unsloth/Qwen3.5-4B-GGUF", "revision": "e87f176479d0855a907a41277aca2f8ee7a09523",
        "vram": 5.75, "ram": 12, "cpu_ram": 16, "cpu_free": 6, "context": 3072,
    },
    {
        "id": "qwen-9b", "chat_id": "qwen9-stock", "name": "Qwen 3.5 9B · Q4_K_M", "tier": "Balanced",
        "file": "Qwen3.5-9B-Q4_K_M.gguf", "size": 5680522464,
        "repo": "unsloth/Qwen3.5-9B-GGUF", "revision": "3885219b6810b007914f3a7950a8d1b469d598a5",
        "vram": 9.75, "ram": 16, "cpu_ram": None, "context": 4096,
    },
    {
        "id": "gemma-12b", "chat_id": "gemma12", "name": "Gemma 4 12B IT · Q4_0", "tier": "Higher capacity",
        "file": "gemma-4-12B-it-Q4_0.gguf", "size": 7219673216,
        "repo": "ggml-org/gemma-4-12B-it-GGUF", "revision": "790d826c6ec7dc8aa0ab23af33e5b8313140a231",
        "vram": 13.75, "ram": 24, "cpu_ram": None, "context": 4096,
    },
)


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint32), ("load", ctypes.c_uint32),
        ("total_phys", ctypes.c_uint64), ("avail_phys", ctypes.c_uint64),
        ("total_page", ctypes.c_uint64), ("avail_page", ctypes.c_uint64),
        ("total_virtual", ctypes.c_uint64), ("avail_virtual", ctypes.c_uint64),
        ("avail_extended", ctypes.c_uint64),
    ]


class AdapterDescription(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_wchar * 128), ("vendor", ctypes.c_uint32),
        ("device", ctypes.c_uint32), ("subsys", ctypes.c_uint32), ("revision", ctypes.c_uint32),
        ("dedicated", ctypes.c_size_t), ("system", ctypes.c_size_t), ("shared", ctypes.c_size_t),
        ("luid_low", ctypes.c_uint32), ("luid_high", ctypes.c_int32), ("flags", ctypes.c_uint32),
    ]


def com_method(instance, index, result, *args):
    table = ctypes.cast(instance, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *args)(table[index])


def video_adapters():
    """DXGI reports dedicated GPU memory as SIZE_T, including values above 4 GiB."""
    factory = ctypes.c_void_p()
    guid = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID("770aae78-f26f-4dba-a829-253c83d1b387").bytes_le)
    create = ctypes.WinDLL("dxgi").CreateDXGIFactory1
    create.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    create.restype = ctypes.c_long
    if create(ctypes.byref(guid), ctypes.byref(factory)) < 0:
        return []
    adapters = []
    try:
        enumerate_adapter = com_method(factory, 12, ctypes.c_long, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
        for index in range(32):
            adapter = ctypes.c_void_p()
            if enumerate_adapter(factory, index, ctypes.byref(adapter)) < 0:
                break
            try:
                description = AdapterDescription()
                describe = com_method(adapter, 10, ctypes.c_long, ctypes.POINTER(AdapterDescription))
                if describe(adapter, ctypes.byref(description)) >= 0 and not (description.flags & 2):
                    adapters.append({"name": description.name, "dedicated": description.dedicated})
            finally:
                com_method(adapter, 2, ctypes.c_ulong)(adapter)
    finally:
        com_method(factory, 2, ctypes.c_ulong)(factory)
    return adapters


def hardware(model_dir):
    memory = MemoryStatus(length=ctypes.sizeof(MemoryStatus))
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
    try:
        adapters = video_adapters()
    except (OSError, AttributeError):
        adapters = []
    existing = next((p for p in (model_dir, *model_dir.parents) if p.exists()), None)
    try:
        free_disk = shutil.disk_usage(existing).free if existing is not None else None
    except OSError:
        free_disk = None
    return {"ram": memory.total_phys, "free_ram": memory.avail_phys, "adapters": adapters, "free_disk": free_disk}


def recommendations(spec, model_dir):
    gpu = max(spec["adapters"], key=lambda item: item["dedicated"], default=None)
    vram = gpu["dedicated"] / GIB if gpu else 0
    # 8/16/32 GB machines report slightly less usable RAM after reservations.
    ram = spec["ram"] / GIB + 0.5
    free_ram = spec["free_ram"] / GIB
    options = []
    for model in CATALOG:
        path = model_dir / model["file"]
        try:
            installed = path.is_file() and path.stat().st_size == model["size"]
        except OSError:
            installed = False
        fits_gpu = vram >= model["vram"] and ram >= model["ram"]
        fits_cpu = model["cpu_ram"] is not None and ram >= model["cpu_ram"] and free_ram >= model["cpu_free"]
        if not fits_gpu and not fits_cpu:
            continue
        disk_ok = installed or (spec["free_disk"] is not None and spec["free_disk"] >= model["size"] + GIB)
        options.append({
            "id": model["id"], "chat_id": model["chat_id"], "name": model["name"], "tier": model["tier"], "bytes": model["size"],
            "minimum_vram_gib": model["vram"], "minimum_ram_gib": model["ram"] if fits_gpu else model["cpu_ram"],
            "context": model["context"],
            "mode": "gpu" if fits_gpu else "cpu", "installed": installed, "disk_ok": disk_ok,
            "url": f"https://huggingface.co/{model['repo']}/blob/{model['revision']}/{model['file']}",
        })
    usable = [option for option in options if option["disk_ok"]]
    gpu_options = [option for option in usable if option["mode"] == "gpu"]
    recommended = (gpu_options or usable)[-1]["id"] if usable else None
    return {
        "gpu": gpu, "ram": spec["ram"], "free_ram": spec["free_ram"], "free_disk": spec["free_disk"],
        "low_free_ram": free_ram < 2,
        "options": options,
        "recommended": recommended,
    }


def guide(model_dir: Path):
    return recommendations(hardware(model_dir), model_dir)
