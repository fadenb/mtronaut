import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mtronaut.terminal import TerminalSession


class TestTerminalSession:
    """Test the TerminalSession class for PTY process management."""

    @pytest.fixture
    def mock_output_callback(self):
        return AsyncMock()

    @pytest.fixture
    def mock_close_callback(self):
        return AsyncMock()

    def test_terminal_session_creation(self, mock_output_callback, mock_close_callback, event_loop):
        """Test TerminalSession initialization."""
        cmd = ["ping", "localhost"]
        session = TerminalSession(
            cmd=cmd,
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=event_loop
        )

        assert session._cmd == cmd
        assert session._on_output == mock_output_callback
        assert session._on_close == mock_close_callback
        assert session._loop == event_loop
        assert session._process is None
        assert session._read_task is None

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    async def test_start_process_success(self, mock_spawn, mock_output_callback, mock_close_callback):
        """Test successful process start."""
        mock_process = MagicMock()
        mock_spawn.return_value = mock_process

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )

        with patch.object(session, '_read_output_loop', new_callable=AsyncMock):
            session.start()

            mock_spawn.assert_called_once_with(["ping", "localhost"], echo=False, env=None)
            assert session._process == mock_process
            assert session._read_task is not None

            session.stop()
            await asyncio.sleep(0)
            mock_close_callback.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    async def test_start_process_already_started(self, mock_spawn, mock_output_callback, mock_close_callback):
        """Test error when starting an already started session."""
        mock_process = MagicMock()
        mock_spawn.return_value = mock_process

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )
        with patch.object(session, '_read_output_loop', new_callable=AsyncMock):
            session.start()

            with pytest.raises(RuntimeError, match="Session has already been started"):
                session.start()

            session.stop()
            await asyncio.sleep(0)
            mock_close_callback.assert_awaited_once()

    @patch('ptyprocess.PtyProcess.spawn')
    def test_start_process_file_not_found(self, mock_spawn, mock_output_callback, mock_close_callback, event_loop):
        """Test handling of FileNotFoundError when starting process."""
        mock_spawn.side_effect = FileNotFoundError("Command not found")

        session = TerminalSession(
            cmd=["nonexistent_command"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=event_loop
        )

        with pytest.raises(FileNotFoundError):
            session.start()

    @pytest.mark.asyncio
    async def test_stop_process_not_started(self, mock_output_callback, mock_close_callback):
        """Test stopping a session that hasn't been started."""
        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )

        session.stop()
        await asyncio.sleep(0)

        assert session._process is None
        assert session._read_task is None
        mock_close_callback.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    async def test_stop_process_with_running_task(self, mock_spawn, mock_output_callback, mock_close_callback):
        """Test stopping a session with an active read task."""
        mock_process = MagicMock()
        mock_process.isalive.return_value = True
        mock_spawn.return_value = mock_process

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )

        with patch.object(session, '_read_output_loop', new_callable=AsyncMock):
            session.start()
            read_task = session._read_task

            session.stop()
            await asyncio.sleep(0)

            mock_process.close.assert_called_once()
            assert session._process is None
            assert read_task.cancelled()
            mock_close_callback.assert_awaited_once()

    @patch('ptyprocess.PtyProcess.spawn')
    def test_resize_terminal_no_process(self, mock_spawn, mock_output_callback, mock_close_callback, event_loop):
        """Test resizing when no process is running."""
        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=event_loop
        )

        # Should not raise an error
        session.resize(80, 24)

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    async def test_resize_terminal_with_process(self, mock_spawn, mock_output_callback, mock_close_callback):
        """Test resizing terminal with running process."""
        mock_process = MagicMock()
        mock_spawn.return_value = mock_process

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )

        with patch.object(session, '_read_output_loop', new_callable=AsyncMock):
            session.start()
            read_task = session._read_task

            session.resize(120, 30)

            mock_process.setwinsize.assert_called_once_with(30, 120)

            session.stop()
            await asyncio.sleep(0)

            assert read_task.cancelled()
            mock_close_callback.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    @patch('asyncio.to_thread')
    async def test_read_output_loop_with_output(self, mock_to_thread, mock_spawn, mock_output_callback, mock_close_callback):
        """Test the output reading loop with data."""
        mock_process = MagicMock()
        mock_process.isalive.side_effect = [True, True, False]
        mock_spawn.return_value = mock_process

        # Mock the read operation to return data then stop
        async def read_side_effect(*args, **kwargs):
            if read_side_effect.call_count == 1:
                read_side_effect.call_count += 1
                return b"test output"
            raise EOFError
        read_side_effect.call_count = 1
        mock_to_thread.side_effect = read_side_effect

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop()
        )

        session.start()
        read_task = session._read_task

        await read_task

        mock_output_callback.assert_called_with(b"test output")
        mock_close_callback.assert_awaited_once()

    @pytest.mark.asyncio
    @patch('ptyprocess.PtyProcess.spawn')
    async def test_environment_variables(self, mock_spawn, mock_output_callback, mock_close_callback):
        """Test that environment variables are passed to the process."""
        mock_process = MagicMock()
        mock_spawn.return_value = mock_process

        env = {"TERM": "xterm-256color", "CUSTOM_VAR": "value"}

        session = TerminalSession(
            cmd=["ping", "localhost"],
            on_output=mock_output_callback,
            on_close=mock_close_callback,
            loop=asyncio.get_running_loop(),
            env=env
        )

        with patch.object(session, '_read_output_loop', new_callable=AsyncMock):
            session.start()
            mock_spawn.assert_called_once_with(["ping", "localhost"], echo=False, env=env)
            session.stop()
            await asyncio.sleep(0)
            mock_close_callback.assert_awaited_once()