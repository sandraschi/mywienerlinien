import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

interface FleetApp {
	id: string;
	name: string;
	description: string;
	backend_port?: number;
	frontend_port?: number;
}

export default function AppsPage() {
	const [apps, setApps] = useState<FleetApp[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch(`${API_BASE}/api/fleet/apps`)
			.then((r) => {
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				return r.json();
			})
			.then((d) => setApps(d.apps ?? []))
			.catch((e) => setError(String(e)))
			.finally(() => setLoading(false));
	}, []);

	return (
		<div className="mx-auto max-w-3xl space-y-4" data-testid="apps-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Apps Hub</h1>
				<p className="mt-1 text-sm text-slate-300">
					Fleet webapps discovered live from this backend. Unknown apps land in
					Experimental.
				</p>
			</div>
			{loading && (
				<div className="animate-pulse py-8 text-center text-sm text-slate-300">
					Loading…
				</div>
			)}
			{error && (
				<div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
					{error}
				</div>
			)}
			{!loading && !error && apps.length === 0 && (
				<div className="py-8 text-center text-sm text-slate-300">
					No apps registered.
				</div>
			)}
			<ul className="space-y-2">
				{apps.map((a) => (
					<li
						key={a.id}
						data-testid={`fleet-app-${a.id}`}
						className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3"
					>
						<span className="text-sm font-semibold text-white">{a.name}</span>
						<p className="mt-0.5 text-sm text-slate-300">{a.description}</p>
						<p className="mt-1 font-mono text-sm text-slate-400">
							{a.backend_port ? `backend :${a.backend_port}` : ""}
							{a.frontend_port ? ` · frontend :${a.frontend_port}` : ""}
						</p>
					</li>
				))}
			</ul>
		</div>
	);
}
