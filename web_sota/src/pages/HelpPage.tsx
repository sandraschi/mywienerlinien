import { Link } from "react-router-dom";

const SECTIONS = [
	{
		title: "Getting started",
		body: "Database: docker compose up -d db (postgres on 5433, named volume). Map: just map (native, port 10722). Dashboard backend: just serve (port 11170). Open this dashboard and check the backend dot in the header. Full walkthrough: docs/ONBOARDING.md in the repo.",
	},
	{
		title: "Where does the data come from?",
		body: "Departures, disruptions, and news come live from the Wiener Linien open data API (no key needed). The stop table and line catalog are reference snapshots from the official GTFS feed. Wiener Linien publishes no live vehicle GPS - map markers are schedule-interpolated.",
	},
	{
		title: "Chat and local LLMs",
		body: "Install Ollama and pull any model (e.g. llama3.2:3b), or start LM Studio. The Settings page auto-detects them. Your keys and prompts never leave this machine: the browser only talks to the backend proxy.",
	},
	{
		title: "MCP server (Claude Desktop)",
		body: "The same transit data is exposed as 15 MCP tools over stdio (see Tools). Configure Claude Desktop with python -m frontend.mcp_server.server and PYTHONPATH pointing at the repo. Docs: docs/TOOLS.md.",
	},
	{
		title: "Troubleshooting",
		body: "Backend dot red? The API on 127.0.0.1:11170 is not running - start it with just serve. Empty departures? The OGD API may be rate-limiting; wait 60 seconds.",
	},
];

export default function HelpPage() {
	return (
		<div className="mx-auto max-w-3xl space-y-4" data-testid="help-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Help</h1>
				<p className="mt-1 text-sm text-slate-300">
					What this dashboard does and how to run it. Repo docs live in{" "}
					<span className="font-mono">docs/</span>.
				</p>
			</div>
			{SECTIONS.map((s) => (
				<section
					key={s.title}
					className="rounded-xl border border-white/10 bg-slate-900/60 p-5"
				>
					<h2 className="font-semibold text-white">{s.title}</h2>
					<p className="mt-1 text-sm leading-relaxed text-slate-300">
						{s.body}
					</p>
				</section>
			))}
			<p className="text-sm text-slate-400">
				Still stuck? Check{" "}
				<Link to="/logs" className="text-blue-300 hover:underline">
					Logs
				</Link>{" "}
				for backend errors, or read{" "}
				<span className="font-mono">docs/TROUBLESHOOTING.md</span>.
			</p>
		</div>
	);
}
