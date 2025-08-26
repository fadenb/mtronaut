import asyncio
import socket
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from mtronaut.session import SessionManager
from mtronaut.terminal import TerminalSession
from mtronaut.tools import ToolParameter, validate_target


class TestEdgeCases:
    """Targeted tests for specific edge cases and uncovered lines."""

    # ---- session.py coverage --- #

    def test_session_manager_remove_nonexistent_connection(self):
        """Test SessionManager.remove() with a connection_id that doesn't exist."""
        manager = SessionManager()
        # This should not raise an error
        manager.remove("nonexistent_conn_id", "some_session_id")

    def test_session_manager_cleanup_connection_with_error(self):
        """Test SessionManager.cleanup_connection() when a terminal stop fails."""
        manager = SessionManager()
        mock_loop = MagicMock()
        
        # Create a session
        rec = manager.create_session(
            connection_id="conn1",
            tool="ping",
            target="localhost",
            cmd=["ping", "localhost"],
            on_output=AsyncMock(),
            on_close=AsyncMock(),
            loop=mock_loop
        )

        # Mock the terminal's stop method to raise an exception
        rec.terminal.stop = MagicMock(side_effect=Exception("Stop failed"))

        # This should not raise an error
        manager.cleanup_connection("conn1")
        rec.terminal.stop.assert_called_once()

    # --- terminal.py coverage --- #

    @pytest.mark.asyncio
    async def test_terminal_read_loop_generic_exception(self):
        """Test that the read loop handles and exits on a generic exception."""
        mock_on_close = AsyncMock()
        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=AsyncMock(),
            on_close=mock_on_close,
            loop=asyncio.get_running_loop()
        )

        # Mock the process and read call to raise an exception
        session._process = MagicMock()
        with patch('asyncio.to_thread', side_effect=Exception("Test Exception")):
            await session._read_output_loop()
        
        # The close callback should still be called
        mock_on_close.assert_awaited_once()

    # --- tools.py coverage --- #

    def test_tool_parameter_validator(self):
        """Test ToolParameter.validate with a custom validator function."""
        # Validator that only accepts the string "valid"
        param = ToolParameter(
            name="test", 
            param_type=str, 
            help_text="...", 
            validator=lambda v: v == "valid"
        )
        assert param.validate("valid") is True
        assert param.validate("invalid") is False

    @patch('socket.gethostbyname')
    def test_validate_target_hostname_success(self, mock_gethostbyname):
        """Test validate_target with a valid hostname that resolves."""
        mock_gethostbyname.return_value = "1.2.3.4" # Mock successful resolution
        # Should not raise an error
        validate_target("example.com")
        mock_gethostbyname.assert_called_once_with("example.com")

    @patch('socket.gethostbyname', side_effect=socket.gaierror)
    def test_validate_target_hostname_failure(self, mock_gethostbyname):
        """Test validate_target with a hostname that fails to resolve."""        
        with pytest.raises(ValueError, match="Invalid target"):
            validate_target("unresolvable.domain.xyz")

    def test_validate_target_ipv4(self):
        """Test validate_target with a valid IPv4 address."""
        validate_target("8.8.8.8") # Should not raise

    def test_validate_target_ipv6(self):
        """Test validate_target with a valid IPv6 address."""
        validate_target("2001:4860:4860::8888") # Should not raise
