import threading
import pytest


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
        self.sleeps = []
        self._lock = threading.Lock()

    def monotonic(self):
        with self._lock:
            return self.now

    def sleep(self, seconds):
        with self._lock:
            self.sleeps.append(seconds)
            self.now += seconds

    def advance(self, seconds):
        with self._lock:
            self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()

    monkeypatch.setattr("src.collect.proxy.time.monotonic", fake.monotonic)
    monkeypatch.setattr("src.collect.proxy.time.sleep", fake.sleep)

    return fake
