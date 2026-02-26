export interface FleetApp {
    id: string;
    name: string;
    description: string;
    port: number;
    repo_path: string;
    icon: string;
    category: "Transit" | "Media" | "Infra" | "Control" | "Creative" | "Knowledge";
}

export const FLEET_REGISTRY: FleetApp[] = [
    {
        id: "vienna-live-mcp",
        name: "Vienna Live MCP",
        description: "Transit and location-aware services in Vienna.",
        port: 10878,
        repo_path: "D:/Dev/repos/vienna-live-mcp",
        icon: "TrainFront",
        category: "Transit"
    },
    {
        id: "handbrake-mcp",
        name: "Handbrake MCP",
        description: "Automated media transcoding and pipeline management.",
        port: 10874,
        repo_path: "D:/Dev/repos/handbrake-mcp",
        icon: "Video",
        category: "Media"
    },
    {
        id: "virtualdj-mcp",
        name: "VirtualDJ MCP",
        description: "SOTA VJing and audio orchestration.",
        port: 10876,
        repo_path: "D:/Dev/repos/virtualdj-mcp",
        icon: "Music",
        category: "Media"
    },
    {
        id: "openfang",
        name: "OpenFang",
        description: "Fleet supervisor and modular agentic node controller.",
        port: 10870,
        repo_path: "D:/Dev/repos/openfang",
        icon: "ShieldCheck",
        category: "Infra"
    },
    {
        id: "osc-mcp",
        name: "OSC MCP",
        description: "Real-time control protocol bridge for high-end audio/visual gear.",
        port: 10766,
        repo_path: "D:/Dev/repos/osc-mcp",
        icon: "Waves",
        category: "Control"
    },
    {
        id: "mcywienerlinien",
        name: "MyWienerLinien",
        description: "Premium transit visualization and live mapping for Vienna.",
        port: 10872,
        repo_path: "D:/Dev/repos/mywienerlinien",
        icon: "Map",
        category: "Transit"
    }
];
