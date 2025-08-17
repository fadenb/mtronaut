from __future__ import annotations

"""
Tool configuration system and command construction.

Provides:
- ToolConfig dataclass describing how to run a network tool
- Registry of supported tools (mtr, tracepath, ping, traceroute)
- Input validation for targets (hostname, IPv4, IPv6)
- Command construction helpers

Intended usage:
    cfg = get_tool_config("mtr")
    cmd = build_command("mtr", target="8.8.8.8")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import ipaddress
import re


# Simple but practical hostname pattern (RFC-1123 relaxed):
# - labels: alphanum + hyphen, not starting/ending with hyphen
# - dots separate labels, total length reasonable
# - allow single-label hostnames for local resolution scenarios
_HOST_LABEL = r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
_HOSTNAME_RE = re.compile(rf"^{_HOST_LABEL}(?:\.{_HOST_LABEL})*$")


@dataclass(frozen=True)
class ToolConfig:
    """Describe a tool's base command and default arguments."""
    name: str
    base_cmd: List[str]
    # Description is optional documentation
    description: str = ""
    # Additional default args appended after base_cmd, before target
    default_args: Optional[List[str]] = None
    # Whether a PTY is strongly recommended/required for proper behavior
    requires_pty: bool = False

    def command(self, target: str) -> List[str]:
        """Build the final command list for execution."""
        validate_target(target)
        parts: List[str] = []
        parts.extend(self.base_cmd)
        if self.default_args:
            parts.extend(self.default_args)
        parts.append(target)
        return parts


def is_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False


def is_ipv6(value: str) -> bool:
    try:
        ipaddress.IPv6Address(value)
        return True
    except ValueError:
        return False


def is_hostname(value: str) -> bool:
    # Reject values that look like raw URLs or contain spaces
    if "://" in value or " " in value:
        return False
    # If it contains only digits and dots, treat as IPv4-like and do NOT accept as hostname.
    # This ensures invalid IPv4 like '256.256.256.256' doesn't slip through hostname regex.
    if re.fullmatch(r"[0-9.]+", value):
        return False
    return bool(_HOSTNAME_RE.match(value))


def validate_target(target: str) -> None:
    """Validate a user-supplied target. Accept hostnames, IPv4, and IPv6."""
    if not target or not isinstance(target, str):
        raise ValueError("Target must be a non-empty string")
    if is_ipv4(target) or is_ipv6(target) or is_hostname(target):
        return
    raise ValueError(f"Invalid target: {target!r}")


# Registry of supported tools
_TOOL_REGISTRY: Dict[str, ToolConfig] = {
    # Default interactive mode (not curses, not report)
    "mtr": ToolConfig(
        name="mtr",
        base_cmd=["mtr"],
        # Use 1s interval as per architecture docs
        default_args=["--interval=1"],
        description="MTR default interactive mode with 1s interval",
        requires_pty=True,
    ),
    "tracepath": ToolConfig(
        name="tracepath",
        base_cmd=["tracepath"],
        description="Tracepath path MTU discovery",
        requires_pty=False,
    ),
    "ping": ToolConfig(
        name="ping",
        base_cmd=["ping"],
        # Limit count for short sessions as per docs
        default_args=["-c", "10"],
        description="Ping with limited count for short sessions",
        requires_pty=False,
    ),
    "traceroute": ToolConfig(
        name="traceroute",
        base_cmd=["traceroute"],
        # Use ICMP probe to avoid requiring root privileges
        default_args=["-I"],
        description="Traceroute hop-by-hop route discovery (ICMP)",
        requires_pty=False,
    ),
}


def get_tool_config(name: str) -> ToolConfig:
    """Lookup a tool configuration by name (case-insensitive)."""
    key = name.lower()
    if key not in _TOOL_REGISTRY:
        raise KeyError(f"Unknown tool: {name!r}. Supported: {', '.join(sorted(_TOOL_REGISTRY))}")
    return _TOOL_REGISTRY[key]


def list_tools() -> List[str]:
    """List supported tool names."""
    return sorted(_TOOL_REGISTRY.keys())


def build_command(tool: str, target: str) -> List[str]:
    """Convenience wrapper to construct a full command for a given tool and target."""
    cfg = get_tool_config(tool)
    return cfg.command(target)