import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

interface Skill {
	name: string;
	description: string;
}

export default function SkillsPage() {
	const [skills, setSkills] = useState<Skill[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		fetch(`${API_BASE}/api/skills`)
			.then((r) => {
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				return r.json();
			})
			.then((d) => setSkills(d.skills ?? []))
			.catch((e) => setError(String(e)))
			.finally(() => setLoading(false));
	}, []);

	return (
		<div className="mx-auto max-w-3xl space-y-4" data-testid="skills-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Skills</h1>
				<p className="mt-1 text-sm text-slate-300">
					Skill packs the chat loads as system context. Served live by the
					backend.
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
			{!loading && !error && skills.length === 0 && (
				<div className="py-8 text-center text-sm text-slate-400">
					No skills published.
				</div>
			)}
			<ul className="space-y-2">
				{skills.map((s) => (
					<li
						key={s.name}
						data-testid={`skill-${s.name}`}
						className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3"
					>
						<span className="font-mono text-sm font-semibold text-blue-300">
							{s.name}
						</span>
						<p className="mt-0.5 text-sm text-slate-300">{s.description}</p>
					</li>
				))}
			</ul>
		</div>
	);
}
