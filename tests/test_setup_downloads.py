"""Exercise interrupted HTTP transfers and non-destructive setup reruns locally."""
import hashlib
import http.server
import importlib.util
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("tf_setup_tests", ROOT / "setup.py")
setup = importlib.util.module_from_spec(spec); sys.modules[spec.name] = setup; spec.loader.exec_module(setup)


class SetupDownloads(unittest.TestCase):
    def test_interrupted_transfer_resumes_and_rerun_preserves_file(self):
        data = bytes(range(256)) * (16384 + 1)
        ranges = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                value = self.headers.get("Range")
                ranges.append(value)
                start = int(value.removeprefix("bytes=").removesuffix("-")) if value else 0
                self.send_response(206 if value else 200)
                self.send_header("Content-Length", str(len(data)-start))
                if value: self.send_header("Content-Range", f"bytes {start}-{len(data)-1}/{len(data)}")
                self.end_headers()
                if len(ranges) == 1:
                    self.wfile.write(data[:1048576]); self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR); self.connection.close()
                else:
                    self.wfile.write(data[start:])
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server, tempfile.TemporaryDirectory() as tmp:
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            asset = setup.Asset("fixture.gguf", f"http://127.0.0.1:{server.server_port}/fixture", len(data), hashlib.sha256(data).hexdigest())
            folder = Path(tmp)
            try:
                with self.assertRaisesRegex(OSError, "Download paused"):
                    setup.download(asset, folder, lambda _: None)
                part = folder / (asset.name + ".tandemforge.part")
                self.assertEqual(part.stat().st_size, 1048576)
                target = setup.download(asset, folder, lambda _: None)
                self.assertTrue(setup.matches(target, asset))
                self.assertIn("bytes=1048576-", ranges)
                stamp = target.stat().st_mtime_ns
                setup.download(asset, folder, lambda _: None)
                self.assertEqual(target.stat().st_mtime_ns, stamp)
                self.assertFalse(part.exists())
            finally:
                server.shutdown(); thread.join()

    def test_bad_existing_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); target = folder / "user.gguf"; target.write_bytes(b"keep")
            asset = setup.Asset(target.name, "http://127.0.0.1:1/unused", 4, hashlib.sha256(b"good").hexdigest())
            with self.assertRaisesRegex(OSError, "existing file differs"):
                setup.download(asset, folder, lambda _: None)
            self.assertEqual(target.read_bytes(), b"keep")

    def test_failed_selection_keeps_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); connections = folder / "connections.json"
            original = b'{"model_dir":"old-models","custom":"keep"}\n'; connections.write_bytes(original)
            bad = setup.Asset("fixture.gguf", "http://127.0.0.1:1/unreachable", 1, "0"*64)
            (folder / bad.name).write_bytes(b"x")
            plan = dict(llama_asset=None, llama_existing=None, models=(bad,), model_dir=folder,
                        starter=None, comfy_asset=None, comfy_url=None, comfy_models=None,
                        image_pack=False, tailscale=False, cpu_comfy=False)
            with patch.object(setup, "DATA", folder), patch.object(setup, "PREFERENCES", connections):
                with self.assertRaises(OSError): setup.install(plan, lambda _: None)
            self.assertEqual(connections.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
