"""Simple sliding-window rate limit, so spam can't burn the $2 API budget.

Kept in memory on purpose: losing these counters on restart is harmless.
"""
import threading
import time
from collections import defaultdict, deque

PER_USER_PER_MINUTE = 30
GLOBAL_PER_MINUTE = 150

_lock = threading.Lock()
_user_hits: dict[str, deque] = defaultdict(deque)
_global_hits: deque = deque()


def _prune(hits: deque, now: float) -> None:
    while hits and now - hits[0] > 60:
        hits.popleft()


def allow_request(user_id: str) -> bool:
    now = time.monotonic()
    with _lock:
        user_hits = _user_hits[user_id]
        _prune(user_hits, now)
        _prune(_global_hits, now)
        if len(user_hits) >= PER_USER_PER_MINUTE or len(_global_hits) >= GLOBAL_PER_MINUTE:
            return False
        user_hits.append(now)
        _global_hits.append(now)
        return True
