import asyncio
import ptyprocess
import shlex
from typing import Callable, Coroutine, List, Dict, Any

# A simple type hint for the callback function that handles output
OutputCallback = Callable[[bytes], Coroutine[Any, Any, None]]
CloseCallback = Callable[[], Coroutine[Any, Any, None]]

class TerminalSession:
    """Manages a single pseudo-terminal (PTY) session for running a command."""

    def __init__(
        self,
        cmd: List[str],
        on_output: OutputCallback,
        on_close: CloseCallback,
        loop: asyncio.AbstractEventLoop
    ):
        self._cmd = cmd
        self._on_output = on_output
        self._on_close = on_close
        self._loop = loop
        self._process: ptyprocess.PtyProcess | None = None
        self._read_task: asyncio.Task | None = None # To manage the async read loop

    def start(self) -> None:
        """Starts the process in a new PTY."""
        if self._process is not None:
            raise RuntimeError("Session has already been started.")

        try:
            self._process = ptyprocess.PtyProcess.spawn(self._cmd, echo=False)
            # Start the asynchronous reader loop
            self._read_task = self._loop.create_task(self._read_output_loop())
        except (FileNotFoundError, ptyprocess.PtyProcessError) as e:
            raise

    def stop(self) -> None:
        """Stops the running process."""
        if self._read_task:
            self._read_task.cancel()
            self._read_task = None
        if self._process and self._process.isalive():
            self._process.close() # Use close for more robust termination
        self._process = None

    def resize(self, cols: int, rows: int) -> None:
        """Resizes the pseudo-terminal window."""
        if self._process:
            self._process.setwinsize(rows, cols)

    async def _read_output_loop(self) -> None:
        """Continuously reads data from the PTY and calls the async output handler."""
        while self._process and self._process.isalive():
            try:
                output = await asyncio.to_thread(self._process.read, 1024)
                if output:
                    await self._on_output(output)
                else:
                    await asyncio.sleep(0.01) # Give process time to produce output
            except (IOError, EOFError):
                break # Process likely exited or PTY closed
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in _read_output_loop (main loop): {e}")
                break

        # Process is no longer alive, or an error occurred. Now, drain any remaining output.
        if self._process:
            while True:
                try:
                    remaining_output = await asyncio.to_thread(self._process.read, 1024)
                    if remaining_output:
                        await self._on_output(remaining_output)
                    else:
                        break # No more remaining output
                except (IOError, EOFError):
                    break # PTY closed during draining
                except Exception as e:
                    print(f"Error in _read_output_loop (draining loop): {e}")
                    break
        # HACK: This is a workaround for a race condition where the process
        # exits and isalive() returns False before all output has been
        # written to the PTY's buffer. The draining loop above helps, but
        # some tools (like tracepath) can still have trailing output that
        # gets missed. A small, fixed delay gives the buffer time to
        # flush before we send the "Process finished" message.
        await asyncio.sleep(0.1)
        await self._on_close()