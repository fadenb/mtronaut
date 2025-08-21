import pytest

from mtronaut.tools import (
    get_tool_config,
    list_tools,
    build_command,
)

# Target validation is exercised via build_command() which calls validate_target()


@pytest.mark.parametrize(
    "tool,target,expected",
    [
        # Ping with default count and packetSize
        ("ping", "8.8.8.8", ["ping", "-c10", "-s56", "-D", "8.8.8.8"]),
        # Traceroute with default count, maxHops, and icmp
        ("traceroute", "1.1.1.1", ["traceroute", "-q3", "-m30", "-I", "--resolve-hostnames", "1.1.1.1"]),
        # Tracepath with default maxHops
        ("tracepath", "example.com", ["tracepath", "-m30", "example.com"]),
        # MTR with default parameters (now includes -b)
        ("mtr", "2001:4860:4860::8888", ["mtr", "-b", "2001:4860:4860::8888"]),
    ],
)
def test_build_command_valid(tool, target, expected):
    cmd = build_command(tool, target)
    assert cmd == expected


@pytest.mark.parametrize(
    "target",
    [
        "",
        "   ",
        "http://not-allowed",
        "space in host",
        "@invalid!",
        "256.256.256.256",  # invalid IPv4
        "12345::1::1",      # invalid IPv6
        "-startshy.example.com",  # invalid hostname label
        "enddash-.example.com",   # invalid hostname label
    ],
)
def test_build_command_invalid_targets(target):
    with pytest.raises(ValueError):
        build_command("ping", target)


def test_get_tool_config_known():
    cfg = get_tool_config("PING")  # case-insensitive
    assert cfg.name == "ping"
    assert "ping" in list_tools()


def test_get_tool_config_unknown():
    with pytest.raises(KeyError):
        get_tool_config("unknown-tool-xyz")