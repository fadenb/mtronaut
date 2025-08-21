from __future__ import annotations

"""
Session management for PTY tool processes.

Provides:
- SessionManager: track TerminalSession instances by connection_id and session_id
- Simple lifecycle helpers for create/start/stop/cleanup
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional
from uuid import uuid4

from mtronaut.terminal import TerminalSession, OutputCallback, CloseCallback


@dataclass
class SessionRecord:
    session_id: str
    terminal: TerminalSession
    tool: str
    target: str


class SessionManager:
    """
    Tracks TerminalSession instances per connection.
    Allows multiple sessions per connection, but does not require it.
    """

    def __init__(self) -> None:
        # connection_id -> session_id -> SessionRecord
        self._by_conn: Dict[str, Dict[str, SessionRecord]] = {}

    def create_session(
        self,
        connection_id: str,
        tool: str,
        target: str,
        cmd: list[str],
        *,
        on_output: OutputCallback,
        on_close: CloseCallback,
        loop,
        params: Optional[Dict[str, Any]] = None, # Add params to signature
    ) -> SessionRecord:
        session_id = str(uuid4())
        # Set TERM environment variable for the terminal session
        env = {"TERM": "xterm-256color"}
        term = TerminalSession(cmd=cmd, on_output=on_output, on_close=on_close, loop=loop, params=params, env=env) # Pass params and env to TerminalSession
        rec = SessionRecord(session_id=session_id, terminal=term, tool=tool, target=target)
        self._by_conn.setdefault(connection_id, {})[session_id] = rec
        return rec

    def get(self, connection_id: str, session_id: str) -> Optional[SessionRecord]:
        return self._by_conn.get(connection_id, {}).get(session_id)

    def list(self, connection_id: str) -> Dict[str, SessionRecord]:
        return dict(self._by_conn.get(connection_id, {}))

    def stop(self, connection_id: str, session_id: str) -> None:
        rec = self.get(connection_id, session_id)
        if rec:
            rec.terminal.stop()

    def remove(self, connection_id: str, session_id: str) -> None:
        bucket = self._by_conn.get(connection_id)
        if not bucket:
            return
        bucket.pop(session_id, None)
        if not bucket:
            self._by_conn.pop(connection_id, None)

    def cleanup_connection(self, connection_id: str) -> None:
        bucket = self._by_conn.pop(connection_id, {})
        for rec in bucket.values():
            try:
                rec.terminal.stop()
            except Exception:
                pass