import { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";
import { useLlmStore } from "../store/llm";

export default function SettingsPage() {
	const {
		providers,
		providerId,
		model,
		setProviders,
		setProviderId,
		setModel,
		setDetected,
	} = useLlmStore();
	const [models, setModels] = useState<string[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [testResult, setTestResult] = useState<string | null>(null);
	const [testing, setTesting] = useState(false);

	useEffect(() => {
		fetch(`${API_BASE}/api/llm/providers`)
			.then((r) => {
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				return r.json();
			})
			.then((d) => {
				const list = d.providers ?? [];
				setProviders(list);
				setDetected(
					list.some((p: { models: string[] }) => (p.models ?? []).length > 0),
				);
				const active =
					list.find((p: { id: string }) => p.id === providerId) ?? list[0];
				if (active) {
					setModels(active.models ?? []);
					if (!model && (active.models ?? []).length > 0)
						setModel(active.models[0]);
				}
			})
			.catch((e) => setError(String(e)))
			.finally(() => setLoading(false));
	}, [providerId, model, setProviders, setDetected, setModel]);

	function pickProvider(id: string) {
		setProviderId(id);
		const active = providers.find((p) => p.id === id);
		setModels(active?.models ?? []);
		if ((active?.models ?? []).length > 0) setModel(active!.models[0]);
	}

	async function testProvider() {
		setTesting(true);
		setTestResult(null);
		try {
			const r = await fetch(`${API_BASE}/api/llm/chat`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					provider: providerId,
					model,
					prompt: "Reply with the word OK.",
				}),
			});
			const d = await r.json();
			setTestResult(d.response ?? "(empty)");
		} catch (e) {
			setTestResult(`Failed: ${e}`);
		} finally {
			setTesting(false);
		}
	}

	return (
		<div className="mx-auto max-w-2xl space-y-6" data-testid="settings-page">
			<div>
				<h1 className="text-2xl font-bold text-white">Settings</h1>
				<p className="mt-1 text-sm text-slate-300">
					Local intelligence providers. Free and private: Ollama (:11434) and LM
					Studio (:1234) are auto-detected. The browser never talks to them
					directly - all chat goes through the backend proxy.
				</p>
			</div>

			{loading && (
				<div className="animate-pulse py-8 text-center text-sm text-slate-400">
					Probing providers…
				</div>
			)}
			{error && (
				<div className="rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
					{error}
				</div>
			)}

			{!loading && !error && (
				<>
					<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
						{providers.map((p) => (
							<div
								key={p.id}
								data-testid={`llm-provider-card-${p.id}`}
								className={`rounded-xl border p-4 ${p.id === providerId ? "border-blue-500 bg-blue-950/30" : "border-white/10 bg-slate-900/60"}`}
							>
								<div className="flex items-center gap-2">
									<span
										className={`h-2.5 w-2.5 rounded-full ${(p.models ?? []).length > 0 ? "bg-emerald-500" : "bg-slate-500"}`}
									/>
									<h2 className="font-semibold text-white">{p.label}</h2>
								</div>
								<p className="mt-1 font-mono text-sm text-slate-400">
									{p.base_url}
								</p>
								<p className="mt-1 text-sm text-slate-300">
									{(p.models ?? []).length > 0
										? `${p.models.length} model(s) detected`
										: "Not running - start it to enable chat"}
								</p>
								<button
									type="button"
									data-testid={`llm-key-${p.id}`}
									onClick={() => pickProvider(p.id)}
									className="mt-3 rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800"
								>
									{p.id === providerId ? "Selected" : "Select"}
								</button>
							</div>
						))}
					</div>

					<div>
						<label
							htmlFor="llm-model"
							className="mb-1 block text-sm font-medium text-slate-200"
						>
							Model
						</label>
						<select
							id="llm-model"
							data-testid="llm-model-select"
							value={model}
							onChange={(e) => setModel(e.target.value)}
							className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100"
						>
							{models.length === 0 && (
								<option value="">No models detected</option>
							)}
							{models.map((m) => (
								<option key={m} value={m}>
									{m}
								</option>
							))}
						</select>
					</div>

					<div>
						<button
							type="button"
							data-testid="llm-test"
							onClick={testProvider}
							disabled={testing || models.length === 0}
							className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40"
						>
							{testing ? "Testing…" : "Test provider"}
						</button>
						{testResult && (
							<p className="mt-2 rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3 text-sm text-slate-200">
								{testResult}
							</p>
						)}
					</div>
				</>
			)}
		</div>
	);
}
