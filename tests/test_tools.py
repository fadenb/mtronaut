import pytest

from mtronaut.tools import (
    get_tool_config,
    list_tools,
    build_command,
    ToolParameter, # Import ToolParameter
    ToolConfig # Import ToolConfig
)

# Target validation is exercised via build_command() which calls validate_target()


@pytest.mark.parametrize(
    "tool,target,params,expected",
    [
        # Ping with default count and packetSize
        ("ping", "8.8.8.8", {}, ["ping", "-c10", "-s56", "-D", "8.8.8.8"]),
        # Traceroute with default count, maxHops, and icmp
        ("traceroute", "1.1.1.1", {}, ["traceroute", "-q3", "-m30", "-I", "--resolve-hostnames", "1.1.1.1"]),
        # Tracepath with default maxHops
        ("tracepath", "example.com", {}, ["tracepath", "-m30", "example.com"]),
        # MTR with default parameters (now includes -b)
        ("mtr", "2001:4860:4860::8888", {}, ["mtr", "-b", "2001:4860:4860::8888"]),
        # MTR with --tcp flag
        ("mtr", "google.com", {"tcp": True}, ["mtr", "-b", "--tcp", "google.com"]),
        # Ping with timestamp=False (should not include -D)
        ("ping", "1.2.3.4", {"timestamp": False}, ["ping", "-c10", "-s56", "1.2.3.4"]),
    ],
)
def test__command_valid(tool, target, params, expected):
    cmd = build_command(tool, target, params)
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

def test_tool_parameter_validation_and_formatting():
    # Test ToolParameter.validate (line 38: if not isinstance(value, self.param_type):)
    param_int = ToolParameter(name="test_int", param_type=int, help_text="An int param")
    assert param_int.validate(10) is True
    assert param_int.validate("not_an_int") is False # This should hit line 38

    # Test ToolParameter.format_for_cli (line 45: if callable(self.param_format):)
    def custom_formatter(value):
        return [f"--custom={value}"]

    param_callable_format = ToolParameter(
        name="test_callable",
        param_type=str,
        help_text="Callable format",
        param_format=custom_formatter,
    )
    assert param_callable_format.format_for_cli("value") == ["--custom=value"] # This should hit line 45

def test_tool_config_command_unknown_parameter_direct():
    # Create a dummy ToolConfig with no parameters
    cfg = ToolConfig(name="dummy", base_cmd=["dummy_cmd"], parameters=[])
    with pytest.raises(ValueError):
        cfg.command("8.8.8.8", {"unknown_param": "value"})

def test_boolean_parameter_coverage():
    bool_param_true = ToolParameter(name="flag", param_type=bool, help_text="", param_format="-f")
    bool_param_false = ToolParameter(name="no_flag", param_type=bool, help_text="", param_format="-nf")

    # Test with a boolean parameter set to True
    config_true = ToolConfig(name="test_tool", base_cmd=["test"], parameters=[bool_param_true])
    cmd_true = config_true.command("8.8.8.8", {"flag": True})
    assert cmd_true == ["test", "-f", "8.8.8.8"]

    # Test with a boolean parameter set to False
    config_false = ToolConfig(name="test_tool", base_cmd=["test"], parameters=[bool_param_false])
    cmd_false = config_false.command("8.8.8.8", {"no_flag": False})
    assert cmd_false == ["test", "8.8.8.8"]
