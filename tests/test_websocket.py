import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from unittest.mock import patch

from mtronaut.main import app
from mtronaut import main # Import main to patch build_command

client = TestClient(app)

def test_start_and_stop_tool_manually():
    """
    Tests starting and stopping a long-running tool manually.
    """
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost"
        })

        # Check for the running status
        response = websocket.receive_json()
        assert response["status"] == "running"

        # Check for some initial binary output
        binary_output = websocket.receive_bytes()
        assert isinstance(binary_output, bytes)

        # Stop the tool
        websocket.send_json({"action": "stop_tool"})

        # The server should send a final 'stopped' message. We'll drain the
        # queue to find it, as there might be leftover bytes.
        final_message = None
        client.timeout = 5.0
        while True:
            try:
                message = websocket.receive()
                if "text" in message:
                    final_message = json.loads(message["text"])
                    if final_message.get("status") == "stopped":
                        break
            except WebSocketDisconnect:
                break

        client.timeout = None # Reset to default
        assert final_message is not None
        assert final_message["status"] == "stopped"

def test_process_finishes_naturally():
    """
    Tests a short-lived process that finishes on its own.
    """
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 1}
        })

        # State 1: Running
        response = websocket.receive_json()
        assert response["status"] == "running"

        # State 2: Receiving output and final status
        # We drain the websocket until we get the final status or disconnect.
        output_received = False
        final_message = None
        # Set a timeout on the client to prevent the test from hanging
        client.timeout = 5.0
        while True:
            try:
                message = websocket.receive()
                if "text" in message:
                    final_message = json.loads(message["text"])
                    break
                elif "bytes" in message:
                    output_received = True

            except WebSocketDisconnect:
                break # PTY closed, which is expected

        client.timeout = None # Reset timeout
        assert output_received
        assert final_message is not None
        assert final_message["status"] == "stopped"
        assert "finished" in final_message["message"]

def test_real_time_output_streaming():
    """
    Tests that real-time output is continuously streamed from a running tool.
    """
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "localhost",
            "params": {"count": 5} # Ping 5 times to ensure continuous output
        })

        # State 1: Running
        response = websocket.receive_json()
        assert response["status"] == "running"

        # Accumulate all binary output
        all_output = b""
        final_message = None
        client.timeout = 10.0 # Give enough time for 5 pings
        
        while True:
            try:
                message = websocket.receive()
                if "text" in message:
                    final_message = json.loads(message["text"])
                    if final_message.get("status") == "stopped":
                        break
                elif "bytes" in message:
                    all_output += message["bytes"]
            except WebSocketDisconnect:
                break # Expected when process finishes and connection closes

        client.timeout = None # Reset timeout

        # Assert that a significant amount of output was received
        assert len(all_output) > 100 # Expect more than 100 bytes for 5 pings

        # Assert final status
        assert final_message is not None
        assert final_message["status"] == "stopped"
        assert "finished" in final_message["message"]

def test_invalid_tool():
    """
    Tests that the server rejects an invalid tool name.
    """
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"action": "start_tool", "tool": "rm -rf /"})
        response = websocket.receive_json()
        assert response["status"] == "error"
        assert "not allowed" in response["message"]


def test_start_tool_invalid_target():
    """
    Tests that the server rejects an invalid target for a tool.
    """
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "action": "start_tool",
            "tool": "ping",
            "target": "invalid target with spaces"
        })
        response = websocket.receive_json()
        assert response["status"] == "error"
        assert "Invalid target:" in response["message"]


def test_start_tool_shlex_error():
    """
    Tests that the server handles shlex.split errors during tool startup.
    This covers the fallback shlex.split block in main.py.
    """
    with patch('mtronaut.main.build_command') as mock_build_command:
        # Configure mock to raise a generic ValueError that won't be caught by specific checks
        mock_build_command.side_effect = ValueError("A generic error not specifically handled")

        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "action": "start_tool",
                "tool": "ping",
                "target": "localhost\"" # Malformed target to cause shlex.split error
            })
            response = websocket.receive_json()
            assert response["status"] == "error"
            assert "Invalid target:" in response["message"]
            mock_build_command.assert_called_once()


