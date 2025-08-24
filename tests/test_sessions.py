import json
import time
from fastapi.testclient import TestClient

from mtronaut.main import app

client = TestClient(app)


def drain_until_stopped(websocket, timeout=5.0):
    """
    Drain mixed text/bytes frames until we see a final JSON message with status == 'stopped'.
    Returns the final JSON message.
    """
    print(f"[{time.time():.6f}] drain_until_stopped: Starting to drain messages")
    client.timeout = timeout
    final_message = None
    while True:
        try:
            message = websocket.receive()
            if "text" in message:
                final_message = json.loads(message["text"])
                print(f"[{time.time():.6f}] drain_until_stopped: Received text message: {final_message}")
                if final_message.get("status") == "stopped":
                    print(f"[{time.time():.6f}] drain_until_stopped: Found stopped message, breaking")
                    break
            elif "bytes" in message:
                print(f"[{time.time():.6f}] drain_until_stopped: Received bytes message (length: {len(message['bytes'])})")
        except Exception as e:
            print(f"[{time.time():.6f}] drain_until_stopped: Exception occurred: {e}")
            break
    client.timeout = None
    print(f"[{time.time():.6f}] drain_until_stopped: Finished draining, returning final message")
    return final_message


def test_start_returns_session_id_and_stop_by_id():
    print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: Starting test")
    with client.websocket_connect("/ws") as websocket:
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: WebSocket connected")
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 1}
        })
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: Sent start_tool message")

        # Running response should include session_id
        running = websocket.receive_json()
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: Received running response: {running}")
        assert running["status"] == "running"
        assert "session_id" in running
        session_id = running["session_id"]
        assert isinstance(session_id, str) and session_id

        # Stop explicitly by session_id
        websocket.send_json({"action": "stop_tool", "session_id": session_id})
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: Sent stop_tool message")

        final_message = drain_until_stopped(websocket)
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: drain_until_stopped returned: {final_message}")
        assert final_message is not None
        assert final_message["status"] == "stopped"
        # server includes the session_id with stopped message for disambiguation
        assert final_message.get("session_id") == session_id
        print(f"[{time.time():.6f}] test_start_returns_session_id_and_stop_by_id: Test completed")


def test_cannot_start_second_session_while_one_is_running():
    import time
    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Starting test")
    with client.websocket_connect("/ws") as websocket:
        # Start first
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: WebSocket connected")
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 1}
        })
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Sent first start_tool message")
        
        # Set a timeout for receiving messages
        client.timeout = 5.0
        try:
            running1 = websocket.receive_json()
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received first running response: {running1}")
            assert running1["status"] == "running"
            assert "session_id" in running1
            sid1 = running1["session_id"]
        except Exception as e:
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Exception while receiving first response: {e}")
            raise
        finally:
            client.timeout = None

        # Attempt to start a second session without stopping the first
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: About to send second start_tool message")
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 1}
        })
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Sent second start_tool message")
        
        # Try to receive the error response
        client.timeout = 5.0
        try:
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: About to receive error response")
            # We need to handle both text and binary messages
            message_count = 0
            while message_count < 10:  # Limit the number of messages we'll process
                print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Waiting for message {message_count}")
                message = websocket.receive()
                message_count += 1
                print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received message {message_count}: {message.keys() if isinstance(message, dict) else type(message)}")
                if "text" in message:
                    resp2 = json.loads(message["text"])
                    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received text message: {resp2}")
                    if resp2.get("status") == "error":
                        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received error response: {resp2}")
                        assert "already running" in resp2["message"]
                        break
                    else:
                        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received non-error text message: {resp2}")
                elif "bytes" in message:
                    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received bytes message (length: {len(message['bytes'])})")
                else:
                    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Received unexpected message type: {message}")
            else:
                print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Exceeded message count limit")
        except Exception as e:
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Exception while receiving error response: {e}")
            raise
        finally:
            client.timeout = None

        # Stop the first session without specifying session_id (defaults to current)
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: About to send stop_tool message")
        websocket.send_json({"action": "stop_tool"})
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Sent stop_tool message")
        
        # Try to drain messages with more detailed debugging
        try:
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: About to call drain_until_stopped")
            client.timeout = 5.0
            final_message = None
            message_count = 0
            while message_count < 20:  # Increase limit for debugging
                print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Waiting for message {message_count}")
                try:
                    message = websocket.receive()
                    message_count += 1
                    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Received message {message_count}: {message.keys() if isinstance(message, dict) else type(message)}")
                    if "text" in message:
                        final_message = json.loads(message["text"])
                        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Received text message: {final_message}")
                        if final_message.get("status") == "stopped":
                            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Found stopped message, breaking")
                            break
                    elif "bytes" in message:
                        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Received bytes message (length: {len(message['bytes'])})")
                    else:
                        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Received unexpected message type: {message}")
                except Exception as e:
                    print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Exception occurred: {e}")
                    break
            client.timeout = None
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: drain - Finished draining, final message: {final_message}")
            
            # Assertions
            assert final_message is not None
            assert final_message["status"] == "stopped"
            assert final_message.get("session_id") == sid1
        except Exception as e:
            print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Exception in drain: {e}")
            raise
            
        print(f"[{time.time():.6f}] test_cannot_start_second_session_while_one_is_running: Test completed")


def test_resize_with_explicit_session_id_no_error():
    # This test ensures the resize_terminal action with session_id is accepted.
    print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: Starting test")
    with client.websocket_connect("/ws") as websocket:
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: WebSocket connected")
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 1}
        })
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: Sent start_tool message")
        running = websocket.receive_json()
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: Received running response: {running}")
        assert running["status"] == "running"
        sid = running["session_id"]

        # Issue a resize with explicit session_id (no response expected, but should not error)
        websocket.send_json({
            "action": "resize_terminal",
            "session_id": sid,
            "term_cols": 100,
            "term_rows": 40
        })
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: Sent resize_terminal message")

        # Drain until final stopped message to complete the session
        final = drain_until_stopped(websocket)
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: drain_until_stopped returned: {final}")
        assert final is not None
        assert final["status"] == "stopped"
        assert final.get("session_id") == sid
        print(f"[{time.time():.6f}] test_resize_with_explicit_session_id_no_error: Test completed")


def test_multiple_concurrent_connections_run_independently():
    print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Starting test")
    with client.websocket_connect("/ws") as ws1, \
         client.websocket_connect("/ws") as ws2:
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Both WebSockets connected")

        # Start a tool on the first connection
        ws1.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 5}
        })
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Sent start_tool message to ws1")
        running1 = ws1.receive_json()
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Received running response from ws1: {running1}")
        assert running1["status"] == "running"
        assert "session_id" in running1
        sid1 = running1["session_id"]

        # Start a tool on the second connection
        ws2.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 5}
        })
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Sent start_tool message to ws2")
        running2 = ws2.receive_json()
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Received running response from ws2: {running2}")
        assert running2["status"] == "running"
        assert "session_id" in running2
        sid2 = running2["session_id"]

        # Ensure session IDs are different
        assert sid1 != sid2
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Session IDs are different: {sid1} != {sid2}")

        # Drain output for both sessions to ensure they complete
        final1 = drain_until_stopped(ws1)
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: drain_until_stopped returned for ws1: {final1}")
        assert final1 is not None
        assert final1["status"] == "stopped"
        assert final1.get("session_id") == sid1

        final2 = drain_until_stopped(ws2)
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: drain_until_stopped returned for ws2: {final2}")
        assert final2 is not None
        assert final2["status"] == "stopped"
        assert final2.get("session_id") == sid2

        # Implicitly, the cleanup_connection in main.py should handle resource cleanup
        # when the websockets are closed by the 'with' statement exiting.
        print(f"[{time.time():.6f}] test_multiple_concurrent_connections_run_independently: Test completed")