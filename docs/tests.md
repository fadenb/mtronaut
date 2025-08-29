# Test Suite Warnings Policy

This document explains the rationale behind the warning filters configured in [pytest.ini](../pytest.ini). The goal is to keep test output clean and actionable while ensuring we do not hide problems that could impact reliability.

We currently apply two targeted filters:

1) PendingDeprecationWarning from python-multipart import style
- What we filter
  - A PendingDeprecationWarning emitted by Starlette/FastAPI’s multipart handling advising a different import style for python-multipart.
- Why it appears
  - This is a known upstream warning in the framework stack during import-time checks for form-data support.
- Why we filter it
  - It is not actionable in this project’s code because we do not directly import or manage python-multipart. The upstream libraries will address this when they move to the new import style.
- Scope and precision
  - The filter is narrowly scoped to the specific warning message about “Please use `import python_multipart` instead.” Only that message is ignored; all other PendingDeprecationWarnings remain visible.

2) DeprecationWarning about PTY forking in a multi-threaded process
- What we filter
  - A DeprecationWarning emitted by the standard library’s pty module when a PTY is spawned in a process that already has multiple threads.
- Why it appears
  - Our tests use Starlette’s TestClient, which runs the ASGI app in a background thread. When the PTY-backed terminal session is created during a test, the interpreter has more than one thread. The stdlib warns because forking within multi-threaded processes can deadlock in some circumstances.
- Why we filter it (and why this is safe)
  - This is a test-environment artifact caused by TestClient’s threading model. In production, the server process can be single-threaded at the time of PTY creation, and this warning does not surface. We want the test output to highlight actionable problems; this particular warning is not a project bug but a byproduct of the testing harness.
- Scope and precision
  - The filter targets only this known PTY deadlock warning by matching the stable portion of its message (“use of forkpty() may lead to deadlocks”) and constraining the module to the stdlib pty module via the filter’s module field. Other DeprecationWarnings are not suppressed.

Reproducing the PTY warning locally
- Run the WebSocket tests with the PTY terminal session enabled under Starlette’s TestClient. The warning appears because the PTY spawn happens after the ASGI app thread has started.
- With our targeted filter in [pytest.ini](../pytest.ini), tests pass cleanly without suppressing unrelated warnings.

Future work to remove the PTY filter entirely
- Move PTY work into a dedicated worker subprocess created via multiprocessing with the “spawn” start method and communicate over pipes/queues. This ensures PTY creation happens in a single-threaded child process.
- Provide a pluggable backend for TerminalSession so tests can use a PIPE-based subprocess backend (no PTY) while production uses PTY. This avoids the warning in tests without changing production behavior.
- Run integration tests against a separately launched server process, avoiding the TestClient threading model in unit tests.

Summary
- We suppress only two known, non-actionable warnings. The filters are scoped to specific messages/modules to avoid hiding other issues. The PTY warning originates from the test harness threading model, not from a defect in our PTY handling. We plan to remove the PTY filter once we refactor the PTY spawn to occur in a single-threaded worker process or adopt a test-only non-PTY backend.