import json
import pytest
from fastapi.testclient import TestClient

from mtronaut.main import app


class TestWebSocketSessions:
    """Tests for WebSocket session management."""

    @pytest.fixture
    def client(self):
        """Provide a TestClient instance for each test."""
        with TestClient(app) as client:
            yield client

    def _drain_until_stopped(self, websocket, client, timeout=5.0):
        """
        Drain mixed text/bytes frames until a final JSON message with status == 'stopped'.
        Returns the final JSON message.
        """
        client.timeout = timeout
        final_message = None
        while True:
            try:
                message = websocket.receive()
                if "text" in message:
                    final_message = json.loads(message["text"])
                    if final_message.get("status") == "stopped":
                        break
                elif "bytes" in message:
                    # Just consume bytes
                    pass
            except Exception:
                break
        client.timeout = None
        return final_message

    def test_start_returns_session_id_and_stop_by_id(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 1}
            })

            running = websocket.receive_json()
            assert running["status"] == "running"
            assert "session_id" in running
            session_id = running["session_id"]
            assert isinstance(session_id, str) and session_id

            websocket.send_json({"action": "stop_tool", "session_id": session_id})

            final_message = self._drain_until_stopped(websocket, client)
            assert final_message is not None
            assert final_message["status"] == "stopped"
            assert final_message.get("session_id") == session_id

    def test_cannot_start_second_session_while_one_is_running(self, client):
        with client.websocket_connect("/ws") as websocket:
            # Start first session
            websocket.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 2}  # This is intentionally a multi-second command. It ensures the first
                                         # session is still active when we try to start a second one. A 2-second
                                         # duration is a safe margin, as the subsequent websocket messages are
                                         # sent and processed in milliseconds.
            })
            running1 = websocket.receive_json()
            assert running1["status"] == "running"
            sid1 = running1["session_id"]

            # Attempt to start a second session
            websocket.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 1}
            })

            # The next message should be an error.
            # Any bytes from the first process are ignored.
            error_response = None
            for _ in range(10): # Try a few times to get past any initial byte chunks
                message = websocket.receive()
                if "text" in message:
                    response = json.loads(message["text"])
                    if response.get("status") == "error":
                        error_response = response
                        break
            
            assert error_response is not None
            assert "already running" in error_response["message"]

            # Stop the first session to clean up
            websocket.send_json({"action": "stop_tool", "session_id": sid1})
            final_message = self._drain_until_stopped(websocket, client)
            assert final_message is not None
            assert final_message["status"] == "stopped"
            assert final_message.get("session_id") == sid1

    def test_resize_with_explicit_session_id_no_error(self, client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 1}
            })
            running = websocket.receive_json()
            assert running["status"] == "running"
            sid = running["session_id"]

            websocket.send_json({
                "action": "resize_terminal",
                "session_id": sid,
                "term_cols": 100,
                "term_rows": 40
            })

            final = self._drain_until_stopped(websocket, client)
            assert final is not None
            assert final["status"] == "stopped"
            assert final.get("session_id") == sid

    def test_multiple_concurrent_connections_run_independently(self, client):
        with client.websocket_connect("/ws") as ws1, \
             client.websocket_connect("/ws") as ws2:

            # Start a tool on the first connection
            ws1.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 2}
            })
            running1 = ws1.receive_json()
            assert running1["status"] == "running"
            sid1 = running1["session_id"]

            # Start a tool on the second connection
            ws2.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost",
                "params": {"count": 2}
            })
            running2 = ws2.receive_json()
            assert running2["status"] == "running"
            sid2 = running2["session_id"]

            assert sid1 != sid2

            # Drain both and check for clean shutdown
            final1 = self._drain_until_stopped(ws1, client)
            assert final1 is not None
            assert final1["status"] == "stopped"
            assert final1.get("session_id") == sid1

            final2 = self._drain_until_stopped(ws2, client)
            assert final2 is not None
            assert final2["status"] == "stopped"
            assert final2.get("session_id") == sid2
