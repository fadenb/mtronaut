// frontend/js/tools.js
// Manages tool-specific configurations and command construction.

const toolConfigurations = {
    "ping": {
        name: "ping",
        defaultTarget: "localhost",
        description: "Send ICMP ECHO_REQUEST packets to network hosts.",
        parameters: [
            { name: "count", param_type: "int", help_text: "Number of pings to send (1-100)", default: 10 },
            { name: "packetSize", param_type: "int", help_text: "Size of packets (bytes)", default: 56 },
            { name: "timestamp", param_type: "bool", help_text: "Print timestamp (-D)", default: true }
        ]
    },
    "mtr": {
        name: "mtr",
        defaultTarget: "8.8.8.8",
        description: "Network diagnostic tool combining traceroute and ping.",
        parameters: [
            { name: "display_asn", param_type: "bool", help_text: "Display AS number (-z)", default: false }
        ]
    },
    "tracepath": {
        name: "tracepath",
        defaultTarget: "google.com",
        description: "Traces path to network host discovering MTU along the way.",
        parameters: [
            { name: "maxHops", param_type: "int", help_text: "Maximum number of hops (TTL)", default: 30 },
            { name: "no_dns_resolution", param_type: "bool", help_text: "Do not resolve hostnames to IPs (-n)", default: false }
        ]
    },
    "traceroute": {
        name: "traceroute",
        defaultTarget: "google.com",
        description: "Prints the route packets take to network host.",
        parameters: [
            { name: "count", param_type: "int", help_text: "Number of probe packets for each hop (1-10)", default: 3 },
            { name: "maxHops", param_type: "int", help_text: "Maximum number of hops (TTL)", default: 30 },
            { name: "icmp", param_type: "bool", help_text: "Use ICMP ECHO for probes (-I)", default: true },
            { name: "resolve_hostnames", param_type: "bool", help_text: "Resolve hostnames", default: true }
        ]
    }
};

window.getToolConfig = function(toolName) {
    return toolConfigurations[toolName];
};

window.listToolNames = function() {
    return Object.keys(toolConfigurations);
};