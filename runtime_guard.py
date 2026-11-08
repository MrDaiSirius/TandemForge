"""Cooperate with other Studio instances before loading models into memory."""
import ctypes
import threading
import time


class RuntimeLease:
    def __init__(self, name="TandemForge-Studio"):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        self.api.CreateMutexW.restype = ctypes.c_void_p
        self.api.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p]
        self.api.CreateEventW.restype = ctypes.c_void_p
        self.api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.api.WaitForSingleObject.restype = ctypes.c_uint32
        for name in ("ReleaseMutex", "SetEvent", "ResetEvent", "CloseHandle"):
            getattr(self.api, name).argtypes = [ctypes.c_void_p]
            getattr(self.api, name).restype = ctypes.c_int
        self.mutex = self.api.CreateMutexW(None, False, f"Local\\{name}-Runtime-v1")
        self.request = self.api.CreateEventW(None, True, False, f"Local\\{name}-Yield-v1")
        self.owner = None
        if not self.mutex or not self.request:
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def acquire(self, update, timeout=600):
        if self.owner == threading.get_ident():
            return
        deadline = time.monotonic() + timeout
        while True:
            result = self.api.WaitForSingleObject(self.mutex, 0)
            if result in (0, 0x80):  # Acquired, or previous process exited.
                self.owner = threading.get_ident()
                self.api.ResetEvent(self.request)
                return
            if result != 0x102:
                raise ctypes.WinError(ctypes.get_last_error())
            self.api.SetEvent(self.request)
            update("Waiting for another local AI workspace / รอแอป Local AI อีกหน้าต่างคืนหน่วยความจำ")
            if time.monotonic() >= deadline:
                raise RuntimeError("Another local AI workspace is still busy. / อีกแอปยังทำงานอยู่ กรุณาลองใหม่")
            time.sleep(0.5)

    def requested(self):
        return self.owner is not None and self.api.WaitForSingleObject(self.request, 0) == 0

    def release(self):
        if self.owner == threading.get_ident():
            if not self.api.ReleaseMutex(self.mutex):
                raise ctypes.WinError(ctypes.get_last_error())
            self.owner = None

    def close(self):
        self.release()
        for name in ("mutex", "request"):
            handle = getattr(self, name, None)
            if handle:
                self.api.CloseHandle(handle)
                setattr(self, name, None)
