import pytest
from unittest.mock import MagicMock, AsyncMock
from mtronaut.session import SessionManager, SessionRecord
from mtronaut.terminal import TerminalSession


class TestSessionManagerUnit:
    """Unit tests for SessionManager class."""

    def test_create_session_with_params(self):
        """Test SessionManager.create_session with params parameter."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Test with params
        params = {"count": 5, "interval": 1}
        cmd = ["ping", "localhost"]
        
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=cmd,
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop,
            params=params
        )
        
        assert isinstance(rec, SessionRecord)
        assert rec.session_id is not None
        assert rec.tool == "ping"
        assert rec.target == "localhost"
        # Verify the session was stored
        assert manager.get("conn1", rec.session_id) == rec

    def test_create_session_without_params(self):
        """Test SessionManager.create_session without params parameter."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Test without params
        cmd = ["ping", "localhost"]
        
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=cmd,
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        assert isinstance(rec, SessionRecord)
        assert rec.session_id is not None
        assert rec.tool == "ping"
        assert rec.target == "localhost"

    def test_get_nonexistent_session(self):
        """Test SessionManager.get with nonexistent session."""
        manager = SessionManager()
        result = manager.get("nonexistent_conn", "nonexistent_session")
        assert result is None

    def test_list_empty_sessions(self):
        """Test SessionManager.list with no sessions."""
        manager = SessionManager()
        result = manager.list("nonexistent_conn")
        assert result == {}

    def test_list_sessions(self):
        """Test SessionManager.list with existing sessions."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Create two sessions
        rec1 = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        rec2 = manager.create_session(
            connection_id="conn1",
            tool="traceroute",
            target="example.com",
            cmd=["traceroute", "example.com"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        # List sessions
        sessions = manager.list("conn1")
        assert len(sessions) == 2
        assert sessions[rec1.session_id] == rec1
        assert sessions[rec2.session_id] == rec2

    def test_stop_nonexistent_session(self):
        """Test SessionManager.stop with nonexistent session."""
        manager = SessionManager()
        # Should not raise an exception
        manager.stop("nonexistent_conn", "nonexistent_session")

    def test_stop_existing_session(self):
        """Test SessionManager.stop with existing session."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Create a session
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        # Mock the terminal stop method
        rec.terminal.stop = MagicMock()
        
        # Stop the session
        manager.stop("conn1", rec.session_id)
        
        # Verify that the terminal stop method was called
        rec.terminal.stop.assert_called_once()

    def test_remove_nonexistent_session(self):
        """Test SessionManager.remove with nonexistent session."""
        manager = SessionManager()
        # Should not raise an exception
        manager.remove("nonexistent_conn", "nonexistent_session")

    def test_remove_nonexistent_connection(self):
        """Test SessionManager.remove with nonexistent connection (bucket is None)."""
        manager = SessionManager()
        # Should not raise an exception - this covers the 'if not bucket: return' branch
        manager.remove("nonexistent_conn", "nonexistent_session")

    def test_remove_last_session_cleanup(self):
        """Test that removing the last session cleans up the connection."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Create a session
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        # Verify session exists
        assert len(manager._by_conn) == 1
        assert len(manager._by_conn["conn1"]) == 1
        
        # Remove the session
        manager.remove("conn1", rec.session_id)
        
        # Verify connection is cleaned up
        assert len(manager._by_conn) == 0

    def test_cleanup_connection_with_multiple_exceptions(self):
        """Test SessionManager.cleanup_connection with multiple exception types."""
        manager = SessionManager()
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        # Create multiple sessions
        rec1 = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        rec2 = manager.create_session(
            connection_id="conn1",
            tool="traceroute",
            target="example.com",
            cmd=["traceroute", "example.com"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        # Mock terminal stop methods to raise different exceptions
        rec1.terminal.stop = MagicMock(side_effect=RuntimeError("Runtime error"))
        rec2.terminal.stop = MagicMock(side_effect=ValueError("Value error"))
        
        # This should not raise any exception
        manager.cleanup_connection("conn1")
        
        # Verify both stop methods were called
        rec1.terminal.stop.assert_called_once()
        rec2.terminal.stop.assert_called_once()

    def test_remove_from_empty_bucket(self):
        """Test SessionManager.remove with a connection that has an empty session dict."""
        manager = SessionManager()
        
        # Add a session first, then remove it to create an empty bucket
        mock_loop = MagicMock()
        mock_on_output = AsyncMock()
        mock_on_close = AsyncMock()
        
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=mock_on_output,
            on_close=mock_on_close,
            loop=mock_loop
        )
        
        # Remove the session, which should leave an empty bucket
        manager.remove("conn1", rec.session_id)
        
        # Now try to remove a nonexistent session from the same connection
        # This should not raise an exception and should clean up the empty bucket
        manager.remove("conn1", "nonexistent_session")
        
        # Verify the connection entry is removed when bucket is empty
        assert "conn1" not in manager._by_conn