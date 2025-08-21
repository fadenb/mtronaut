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

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import ipaddress
import validators

@dataclass(frozen=True)
class ToolParameter:
    """Describes a configurable parameter for a tool."""
    name: str
    param_type: type
    help_text: str
    required: bool = False
    default: Any = None
    # Format string for the command line, e.g., "-i {}" or "--interval={}"
    param_format: str | Callable[[Any], List[str]] = "{}"
    # Validator regex or function
    validator: Callable[[Any], bool] | None = None

    def validate(self, value: Any) -> bool:
        if not isinstance(value, self.param_type):
            return False
        if self.validator:
            return self.validator(value)
        return True

    def format_for_cli(self, value: Any) -> List[str]:
        if callable(self.param_format):
            return self.param_format(value)
        return [self.param_format.format(value)]

@dataclass(frozen=True)
class ToolConfig:
    """Describe a tool's base command and default arguments."""
    name: str
    base_cmd: List[str]
    description: str = ""
    requires_pty: bool = False
    parameters: List[ToolParameter] = field(default_factory=list)

    def command(self, target: str, params: Optional[Dict[str, Any]] = None) -> List[str]:
        """Build the final command list for execution with parameter validation."""
        validate_target(target)
        parts: List[str] = list(self.base_cmd)

        # Start with default parameters
        final_params = {p.name: p.default for p in self.parameters if p.default is not None}

        # Override with explicitly provided parameters
        if params:
            for p_name, p_value in params.items():
                p_config = next((p for p in self.parameters if p.name == p_name), None)
                if not p_config:
                    raise ValueError(f"Unknown parameter: {p_name}")
                if not p_config.validate(p_value):
                    raise ValueError(f"Invalid value for parameter '{p_name}': {p_value}")
                final_params[p_name] = p_value

        # Add parameters to command parts
        for p_config in self.parameters:
            if p_config.name in final_params:
                value = final_params[p_config.name]
                if p_config.param_type == bool:
                    if value: # Only add flag if boolean is True
                        parts.extend(p_config.format_for_cli(value))
                else:
                    parts.extend(p_config.format_for_cli(value))
            elif p_config.required:
                raise ValueError(f"Missing required parameter: {p_config.name}")

        parts.append(target)
        return parts

def validate_target(target: str) -> None:
    """Validate a user-supplied target. Accept hostnames, IPv4, and IPv6."""
    if not target or not isinstance(target, str):
        raise ValueError("Target must be a non-empty string")

    # Use a combined check for IP addresses and hostnames
    is_valid_ip = False
    try:
        ipaddress.ip_address(target)
        is_valid_ip = True
    except ValueError:
        pass

    if is_valid_ip:
        return

    # Fallback to hostname validation if not a valid IP
    if validators.domain(target):
        return

    raise ValueError(f"Invalid target: {target!r}")

# Registry of supported tools
_TOOL_REGISTRY: Dict[str, ToolConfig] = {
    "mtr": ToolConfig(
        name="mtr",
        base_cmd=["mtr", "-b"],
        description="MTR default interactive mode",
        requires_pty=True,
        parameters=[
            ToolParameter(
                name="no_dns_resolution",
                param_type=bool,
                help_text="Do not resolve hostnames to IPs (-n)",
                default=False,
                param_format="-n",
            ),
            ToolParameter(
                name="display_asn",
                param_type=bool,
                help_text="Display AS number (-z)",
                default=False,
                param_format="-z",
            ),
        ],
    ),
    "tracepath": ToolConfig(
        name="tracepath",
        base_cmd=["tracepath"],
        description="Tracepath path MTU discovery",
        requires_pty=False,
        parameters=[
            ToolParameter(
                name="maxHops",
                param_type=int,
                help_text="Maximum number of hops (TTL)",
                default=30,
                param_format="-m{}",
                validator=lambda v: 1 <= v <= 255,
            ),
            ToolParameter(
                name="no_dns_resolution",
                param_type=bool,
                help_text="Do not resolve hostnames to IPs (-n)",
                default=False,
                param_format="-n",
            ),
        ],
    ),
    "ping": ToolConfig(
        name="ping",
        base_cmd=["ping"],
        description="Ping with limited count for short sessions",
        requires_pty=False,
        parameters=[
            ToolParameter(
                name="count",
                param_type=int,
                help_text="Number of pings to send (1-100)",
                default=10,
                param_format="-c{}",
                validator=lambda v: 1 <= v <= 100,
            ),
            ToolParameter(
                name="packetSize",
                param_type=int,
                help_text="Size of packets (bytes)",
                default=56,
                param_format="-s{}",
                validator=lambda v: 1 <= v <= 65507,
            ),
            ToolParameter(
                name="timestamp",
                param_type=bool,
                help_text="Print timestamp (-D)",
                default=True,
                param_format="-D",
            ),
        ],
    ),
    "traceroute": ToolConfig(
        name="traceroute",
        base_cmd=["traceroute"],
        description="Traceroute hop-by-hop route discovery (ICMP)",
        requires_pty=False,
        parameters=[
            ToolParameter(
                name="count",
                param_type=int,
                help_text="Number of probe packets for each hop (1-10)",
                default=3,
                param_format="-q{}",
                validator=lambda v: 1 <= v <= 10,
            ),
            ToolParameter(
                name="maxHops",
                param_type=int,
                help_text="Maximum number of hops (TTL)",
                default=30,
                param_format="-m{}",
                validator=lambda v: 1 <= v <= 255,
            ),
            ToolParameter(
                name="icmp",
                param_type=bool,
                help_text="Use ICMP ECHO for probes (-I)",
                default=True,
                param_format="-I",
            ),
            ToolParameter(
                name="resolve_hostnames",
                param_type=bool,
                help_text="Resolve hostnames",
                default=True,
                param_format="--resolve-hostnames",
            ),
        ],
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

def build_command(tool: str, target: str, params: Optional[Dict[str, Any]] = None) -> List[str]:
    """Convenience wrapper to construct a full command for a given tool and target."""
    cfg = get_tool_config(tool)
    return cfg.command(target, params) # Pass params to cfg.command