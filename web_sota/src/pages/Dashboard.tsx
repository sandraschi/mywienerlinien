import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../common/api";
import { useBackendStatus } from "../hooks/useBackendStatus";
import { API_BASE } from "../lib/api";
import { MAP_URL } from "../lib/config";
import { useLlmStore } from "../store/llm";

const ONBOARD_KEY = "wl_onboarded";

const CARDS = [
	{
		to: "/departures",
		title: "Departures",
		desc: "Live boards for 12 major stops (OGD realtime).",
	},
	{
		to: "/disruptions",
		title: "Disruptions",
		desc: "Live incidents and elevator outages.",
	},
	{ to: "/lines", title: "Lines", desc: "Full Vienna line catalog from GTFS." },
	{
		to: "/chat",
		title: "Chat",
		desc: "Ask about transit with local LLM help.",
	},
	{ to: "/tools", title: "Tools", desc: "MCP tools this dashboard speaks to." },
	{ to: "/logs", title: "Logs", desc: "Backend activity ring buffer." },
];

export default function Dashboard() {
	const backend = useBackendStatus();
	const { detected, probing, setProviders, setDetected, setProbing } =
		useLlmStore();
	const [onboarded, setOnboarded] = useState(
		() => localStorage.getItem(ONBOARD_KEY) === "1",
	);
	const [version, setVersion] = useState("");

	useEffect(() => {
		fetch(`${API_BASE}/api/llm/providers`)
			.then((r) => r.json())
			.then((d) => {
				const providers = d.providers ?? [];
				setProviders(providers);
				setDetected(
					providers.some(
						(p: { models: string[] }) => (p.models ?? []).length > 0,
					),
				);
			})
			.catch(() => setDetected(false))
			.finally(() => setProbing(false));
		api
			.status()
			.then((s) => setVersion(s.version ?? ""))
			.catch(() => {});
	}, [setProviders, setDetected, setProbing]);

	const dot =
		backend === "up"
			? "bg-emerald-500"
			: backend === "down"
				? "bg-red-500"
				: "bg-amber-400 animate-pulse";

	return (
		<div className="space-y-8" data-testid="dashboard">
			{/* Hero */}
			<section className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-950 p-8">
				<p className="text-sm font-semibold uppercase tracking-widest text-blue-300">
					Wiener Linien live dashboard
				</p>
				<h1 className="mt-2 text-3xl font-bold text-white">
					Vienna transit, live from the official open data API
				</h1>
				<p className="mt-2 max-w-2xl text-sm text-slate-300">
					Departure boards, disruptions, and line data for Vienna. No API key
					needed. Vehicle markers on the map are schedule-interpolated - Wiener
					Linien publishes no live GPS positions.
				</p>
				<div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
					<span
						className="inline-flex items-center gap-2 text-slate-200"
						data-testid="backend-dot"
					>
						<span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
						Backend{" "}
						{backend === "up"
							? `connected${version ? ` (v${version})` : ""}`
							: backend}
					</span>
					<span className="inline-flex items-center gap-2 text-slate-200">
						<span
							className={`h-2.5 w-2.5 rounded-full ${probing ? "bg-amber-400 animate-pulse" : detected ? "bg-emerald-500" : "bg-slate-500"}`}
						/>
						{probing
							? "Probing local LLM…"
							: detected
								? "Local LLM available"
								: "No local LLM detected"}
					</span>
					<a
						href={MAP_URL}
						target="_blank"
						rel="noopener noreferrer"
						className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500"
					>
						Open live map
					</a>
				</div>
				{backend === "down" && (
					<div className="mt-4 rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
						Backend unreachable at {API_BASE}. Start it with{" "}
						<span className="font-mono">just serve</span> (port 11170), then
						reload.
					</div>
				)}
				{!onboarded && (
					<div
						className="mt-4 rounded-lg border border-red-700 bg-red-950/40 p-4"
						data-testid="onboarding-cue"
					>
						<p className="text-sm font-semibold text-red-200">
							First time here? 60-second setup
						</p>
						<p className="mt-1 text-sm text-slate-300">
							Start the stack, open this dashboard, optionally start Ollama for
							chat. Full guide:{" "}
							<span className="font-mono">docs/ONBOARDING.md</span>
						</p>
						<div className="mt-3 flex gap-2">
							<Link
								to="/help"
								className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
							>
								Show me how
							</Link>
							<button
								type="button"
								onClick={() => {
									localStorage.setItem(ONBOARD_KEY, "1");
									setOnboarded(true);
								}}
								className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
							>
								Dismiss
							</button>
						</div>
					</div>
				)}
			</section>

			{/* Quick navigation */}
			<section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{CARDS.map((c) => (
					<Link
						key={c.to}
						to={c.to}
						data-testid={`nav-card-${c.to.replace("/", "") || "home"}`}
						className="rounded-xl border border-white/10 bg-slate-900/60 p-5 transition-colors hover:border-blue-500/60 hover:bg-slate-900"
					>
						<h2 className="font-semibold text-white">{c.title}</h2>
						<p className="mt-1 text-sm text-slate-300">{c.desc}</p>
					</Link>
				))}
			</section>
		</div>
	);
}
