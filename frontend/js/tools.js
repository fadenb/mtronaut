// frontend/js/tools.js
// Manages tool-specific configurations and command construction.

const toolConfigurations = {
    "ping": {
        name: "ping",
        defaultTarget: "localhost",
        description: "Send ICMP ECHO_REQUEST packets to network hosts.",
        buildCommand: (target) => ["ping", target]
    },
    "mtr": {
        name: "mtr",
        defaultTarget: "8.8.8.8",
        description: "Network diagnostic tool combining traceroute and ping.",
        buildCommand: (target) => ["mtr", "--interval=1", target]
    },
    "tracepath": {
        name: "tracepath",
        defaultTarget: "google.com",
        description: "Traces path to network host discovering MTU along the way.",
        buildCommand: (target) => ["tracepath", target]
    },
    "traceroute": {
        name: "traceroute",
        defaultTarget: "google.com",
        description: "Prints the route packets take to network host.",
        buildCommand: (target) => ["traceroute", target]
    }
};

function getToolConfig(toolName) {
    return toolConfigurations[toolName];
}

function listToolNames() {
    return Object.keys(toolConfigurations);
}