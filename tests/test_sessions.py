import json
from fastapi.testclient import TestClient

from mtronaut.main import app

client = TestClient(app)


def drain_until_stopped(websocket, timeout=5.0):
    """
    Drain mixed text/bytes frames until we see a final JSON message with status == 'stopped'.
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
        except Exception:
            break
    client.timeout = None
    return final_message


def test_start_returns_session_id_and_stop_by_id():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 1"
        })

        # Running response should include session_id
        running = websocket.receive_json()
        assert running["status"] == "running"
        assert "session_id" in running
        session_id = running["session_id"]
        assert isinstance(session_id, str) and session_id

        # Stop explicitly by session_id
        websocket.send_json({"action": "stop_tool", "session_id": session_id})

        final_message = drain_until_stopped(websocket)
        assert final_message is not None
        assert final_message["status"] == "stopped"
        # server includes the session_id with stopped message for disambiguation
        assert final_message.get("session_id") == session_id


def test_cannot_start_second_session_while_one_is_running():
    with client.websocket_connect("/ws") as websocket:
        # Start first
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 1"
        })
        running1 = websocket.receive_json()
        assert running1["status"] == "running"
        assert "session_id" in running1
        sid1 = running1["session_id"]

        # Attempt to start a second session without stopping the first
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 1"
        })
        resp2 = websocket.receive_json()
        assert resp2["status"] == "error"
        assert "already running" in resp2["message"]

        # Stop the first session without specifying session_id (defaults to current)
        websocket.send_json({"action": "stop_tool"})
        final1 = drain_until_stopped(websocket)
        assert final1 is not None
        assert final1["status"] == "stopped"
        assert final1.get("session_id") == sid1


def test_resize_with_explicit_session_id_no_error():
    # This test ensures the resize_terminal action with session_id is accepted.
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 1"
        })
        running = websocket.receive_json()
        assert running["status"] == "running"
        sid = running["session_id"]

        # Issue a resize with explicit session_id (no response expected, but should not error)
        websocket.send_json({
            "action": "resize_terminal",
            "session_id": sid,
            "term_cols": 100,
            "term_rows": 40
        })

        # Drain until final stopped message to complete the session
        final = drain_until_stopped(websocket)
        assert final is not None
        assert final["status"] == "stopped"
        assert final.get("session_id") == sid


def test_multiple_concurrent_connections_run_independently():
    with client.websocket_connect("/ws") as ws1, \
         client.websocket_connect("/ws") as ws2:

        # Start a tool on the first connection
        ws1.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 5"
        })
        running1 = ws1.receive_json()
        assert running1["status"] == "running"
        assert "session_id" in running1
        sid1 = running1["session_id"]

        # Start a tool on the second connection
        ws2.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost -c 5"
        })
        running2 = ws2.receive_json()
        assert running2["status"] == "running"
        assert "session_id" in running2
        sid2 = running2["session_id"]

        # Ensure session IDs are different
        assert sid1 != sid2

        # Drain output for both sessions to ensure they complete
        final1 = drain_until_stopped(ws1)
        assert final1 is not None
        assert final1["status"] == "stopped"
        assert final1.get("session_id") == sid1

        final2 = drain_until_stopped(ws2)
        assert final2 is not None
        assert final2["status"] == "stopped"
        assert final2.get("session_id") == sid2

        # Implicitly, the cleanup_connection in main.py should handle resource cleanup
        # when the websockets are closed by the 'with' statement exiting.