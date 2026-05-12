"""
session_manager.py
------------------
Controla o número de sessões simultâneas de automação (máximo configurável).
"""

import threading


class SessionManager:
    def __init__(self, max_sessions: int = 5):
        self._max = max_sessions
        self._sessoes: set[str] = set()
        self._lock = threading.Lock()

    def pode_adicionar(self) -> bool:
        with self._lock:
            return len(self._sessoes) < self._max

    def adicionar(self, sid: str) -> None:
        with self._lock:
            self._sessoes.add(sid)

    def remover(self, sid: str) -> None:
        with self._lock:
            self._sessoes.discard(sid)

    @property
    def total(self) -> int:
        with self._lock:
            return len(self._sessoes)
