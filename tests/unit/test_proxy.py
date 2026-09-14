import threading
import pytest

from src.collect.proxy import ProxyRateLimiter


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


@pytest.fixture
def proxies():
    return [
        {"http": f"http://proxy{i}:8080", "https": f"http://proxy{i}:8080"}
        for i in range(3)
    ]


def test_when_under_limit_then_does_not_sleep(clock):
    limiter = ProxyRateLimiter(max_requests=3, sliding_window=1.0)

    for _ in range(3):
        limiter.wait_for_slot()

    assert clock.sleeps == []


def test_sleeps_until_window_is_available_when_limit_is_exceeded(clock):
    limiter = ProxyRateLimiter(max_requests=2, sliding_window=0.5)

    for _ in range(3):
        limiter.wait_for_slot()

    assert clock.sleeps == [pytest.approx(0.5, abs=0.02)]


def test_when_window_elapsed_then_allows_request(clock):
    limiter = ProxyRateLimiter(max_requests=1, sliding_window=0.3)
    limiter.wait_for_slot()

    clock.advance(0.31)
    limiter.wait_for_slot()

    assert clock.sleeps == []


def test_when_each_thread_has_its_own_limiter_then_limit_is_respected(clock):
    limiters = [
        ProxyRateLimiter(max_requests=60, sliding_window=60.0) for _ in range(3)
    ]
    errors = []

    def worker(limiter):
        try:
            for _ in range(90):
                limiter.wait_for_slot()
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=worker, args=(limiters[i % 3],)) for i in range(3)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert not errors

    for limiter in limiters:
        assert len(limiter._timestamps) <= 60
