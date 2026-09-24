import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "../lib/api";

interface NewsItem {
	name: string;
	title: string;
	description: string;
}

interface LogEntry {
	id?: string;
	ts?: string;
	level?: string;
	kind?: string;
	message?: string;
}

export default function InboxPage() {
	const [news, setNews] = useState<NewsItem[]>([]);
	const [logs, setLogs] = useState<LogEntry[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		Promise.all([
			fetch(`${API_BASE}/api/news`).then((r) => {
				if (!r.ok) throw new Error(`news: ${r.status}`);
				return r.json();
			}),
			fetch(`${API_BASE}/api/logs?limit=10&sort=desc`).then((r) => {
				if (!r.ok) throw new Error(`logs: ${r.status}`);
				return r.json();
			}),
		])
			.then(([n, l]) => {
				setNews(n.pois ?? []);
				setLogs(l.entries ?? []);
			})
			.catch((e) => setError(String(e)))
			.finally(() => setLoading(false));
	}, []);

	return (
		<div className="mx-auto max-w-3xl space-y-6" data-testid="inbox-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Inbox</h1>
				<p className="mt-1 text-sm text-slate-300">
					Network news from Wiener Linien plus the latest backend activity.
				</p>
			</div>

			{loading && (
				<div className="animate-pulse py-8 text-center text-sm text-slate-400">
					Loading…
				</div>
			)}
			{error && (
				<div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
					{error}
				</div>
			)}

			{!loading && !error && (
				<>
					<section>
						<h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
							Network news ({news.length})
						</h2>
						{news.length === 0 ? (
							<p className="py-4 text-center text-sm text-slate-400">
								No current news.
							</p>
						) : (
							<ul className="space-y-2">
								{news.slice(0, 20).map((n) => (
									<li
										key={n.name}
										className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3"
									>
										<p className="text-sm font-semibold text-white">
											{n.title || n.name}
										</p>
										{n.description && (
											<p className="mt-0.5 text-sm text-slate-300">
												{n.description}
											</p>
										)}
									</li>
								))}
							</ul>
						)}
					</section>

					<section>
						<div className="mb-2 flex items-center justify-between">
							<h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
								Latest activity
							</h2>
							<Link
								to="/logs"
								className="text-sm text-blue-300 hover:underline"
							>
								All logs
							</Link>
						</div>
						{logs.length === 0 ? (
							<p className="py-4 text-center text-sm text-slate-400">
								No activity yet.
							</p>
						) : (
							<ul className="space-y-1">
								{logs.map((e, i) => (
									<li
										key={e.id ?? i}
										className="font-mono text-sm text-slate-300"
									>
										<span className="text-slate-500">{e.ts ?? ""}</span>{" "}
										<span className="text-blue-300">[{e.kind ?? "?"}]</span>{" "}
										{e.message ?? ""}
									</li>
								))}
							</ul>
						)}
					</section>
				</>
			)}
		</div>
	);
}
