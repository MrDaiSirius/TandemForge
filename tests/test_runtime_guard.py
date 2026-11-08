"""Verify model ownership across Windows processes, including a crashed owner."""
import multiprocessing
import sys
import time
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_guard import RuntimeLease


def contender(name, events):
    lease = RuntimeLease(name)
    lease.acquire(lambda _: events.put("waiting"), timeout=8)
    events.put("acquired")
    lease.close()


def abandoned_owner(name, events):
    lease = RuntimeLease(name)
    lease.acquire(lambda _: None)
    events.put("held")
    time.sleep(20)


@unittest.skipUnless(sys.platform == "win32", "Windows named kernel objects")
class RuntimeGuardTests(unittest.TestCase):
    def test_waiter_requests_release_and_cannot_overlap(self):
        name = "TandemForge-test-" + uuid.uuid4().hex
        lease = RuntimeLease(name)
        lease.acquire(lambda _: None)
        events = multiprocessing.Queue()
        process = multiprocessing.Process(target=contender, args=(name, events))
        process.start()
        try:
            self.assertEqual(events.get(timeout=5), "waiting")
            self.assertTrue(lease.requested())
            lease.release()
            while events.get(timeout=5) != "acquired":
                pass
            process.join(5)
            self.assertEqual(process.exitcode, 0)
        finally:
            if process.is_alive(): process.terminate(); process.join()
            lease.close()

    def test_crashed_owner_does_not_lock_out_next_job(self):
        name = "TandemForge-test-" + uuid.uuid4().hex
        lease = RuntimeLease(name)
        events = multiprocessing.Queue()
        process = multiprocessing.Process(target=abandoned_owner, args=(name, events))
        process.start()
        try:
            self.assertEqual(events.get(timeout=5), "held")
            process.terminate(); process.join(5)
            lease.acquire(lambda _: None, timeout=2)
            self.assertIsNotNone(lease.owner)
        finally:
            if process.is_alive(): process.terminate(); process.join()
            lease.close()


if __name__ == "__main__":
    unittest.main()
