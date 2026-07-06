from collections import deque
import itertools
import threading
import time

WINDOW_SECONDS = 60.0


class ProxyRateLimiter:
    def __init__(self, max_requests, sliding_window):
        self.max_requests = max_requests
        self.sliding_window = sliding_window
        self._timestamps = deque()
        self._thread_lock = threading.Lock()

    def wait_for_slot(self):
        while True:
            with self._thread_lock:
                now = time.monotonic()

                while (
                    self._timestamps and now - self._timestamps[0] > self.sliding_window
                ):
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return

                stop_for = self.sliding_window - (now - self._timestamps[0]) + 0.01

            time.sleep(max(stop_for, 0.01))


class ProxyRouter:
    def __init__(self, proxies, max_spin: int):
        if not proxies:
            raise ValueError("PROXIES está vazio")
        self._proxies = proxies
        self._limiters = [ProxyRateLimiter(max_spin, WINDOW_SECONDS) for _ in proxies]
        self._cycle = itertools.cycle(range(len(proxies)))
        self._lock = threading.Lock()

    def acquire_proxy(self):
        with self._lock:
            i = next(self._cycle)
        proxy = self._proxies[i]
        self._limiters[i].wait_for_slot()
        return proxy, i
