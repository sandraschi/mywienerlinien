import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

interface McpTool {
	name: string;
	description: string;
}

const TOOL_DOCS: McpTool[] = [
	{ name: "help", description: "Usage help for all Vienna transit tools." },
	{
		name: "server_status",
		description: "Server health, API + database status.",
	},
	{ name: "server_shutdown", description: "Request an orderly shutdown." },
	{ name: "list_cities", description: "List configured transit cities." },
	{ name: "switch_to_city", description: "Switch the active city." },
	{
		name: "city_transit_stats",
		description: "Statistics for a city's network.",
	},
	{ name: "station_search", description: "Fuzzy station search by name." },
	{ name: "nearby_stops", description: "Stops near a location." },
	{ name: "next_departures", description: "Live departures for a station." },
	{ name: "traffic_alerts", description: "Active service disruptions." },
	{ name: "line_status", description: "Status of one transit line." },
	{ name: "stop_timetable", description: "Full timetable for a stop." },
	{ name: "journey_planner", description: "A* route planning with transfers." },
	{ name: "show_server_status_card", description: "Prefab UI status card." },
	{ name: "show_departures_card", description: "Prefab UI departures card." },
];

export default function ToolsPage() {
	const [live, setLive] = useState<string[]>([]);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch(`${API_BASE}/api/capabilities`)
			.then((r) => r.json())
			.then((d) => setLive(d.endpoints ?? []))
			.catch((e) => setError(String(e)));
	}, []);

	return (
		<div className="mx-auto max-w-3xl space-y-6" data-testid="tools-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Tools</h1>
				<p className="mt-1 text-sm text-slate-300">
					MCP tools exposed over stdio for Claude Desktop, plus the REST
					endpoints this dashboard uses. Full reference:{" "}
					<span className="font-mono">docs/TOOLS.md</span>.
				</p>
			</div>

			<section>
				<h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
					MCP tools ({TOOL_DOCS.length})
				</h2>
				<ul className="space-y-2">
					{TOOL_DOCS.map((t) => (
						<li
							key={t.name}
							data-testid={`tool-${t.name}`}
							className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3"
						>
							<span className="font-mono text-sm font-semibold text-blue-300">
								{t.name}
							</span>
							<p className="mt-0.5 text-sm text-slate-300">{t.description}</p>
						</li>
					))}
				</ul>
			</section>

			<section>
				<h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
					Live REST endpoints
				</h2>
				{error ? (
					<div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
						Backend unreachable: {error}
					</div>
				) : live.length === 0 ? (
					<div className="animate-pulse py-4 text-sm text-slate-400">
						Loading…
					</div>
				) : (
					<ul className="flex flex-wrap gap-2">
						{live.map((e) => (
							<li
								key={e}
								className="rounded bg-slate-800 px-2 py-1 font-mono text-sm text-slate-200"
							>
								{e}
							</li>
						))}
					</ul>
				)}
			</section>
		</div>
	);
}
